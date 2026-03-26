from functools import lru_cache

from sklearn.metrics import accuracy_score, f1_score

import torch

from sentence_transformers import SentenceTransformer

class SmallClassifier(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim=24, output_dim=2):
        super(SmallClassifier, self).__init__()
        self.sequential = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, output_dim)
        )

    def forward(self, x):
        return self.sequential(x)

@lru_cache(maxsize=1)
def get_sbert_model():
    model = SentenceTransformer("all-MiniLM-L6-v2")
    model.eval()
    return model

try:
    from .dataset_builder import read_dataset, split_dataset
except ImportError:
    from dataset_builder import read_dataset, split_dataset

def prepare_data(dataset_file):
    dataset = read_dataset(dataset_file)
    train_data, test_data = split_dataset(dataset)
    return train_data, test_data

def vectorize_data(train_data, test_data):
    model = get_sbert_model()
    train_texts, train_labels = zip(*train_data)
    test_texts, test_labels = zip(*test_data)

    train_labels = [int(label) for label in train_labels]
    test_labels = [int(label) for label in test_labels]

    train_embeddings = model.encode(train_texts)
    test_embeddings = model.encode(test_texts)

    return train_embeddings, train_labels, test_embeddings, test_labels

def train_model(train_embeddings, train_labels, epoch):
    input_dim = train_embeddings.shape[1]
    print(f"Input dimension: {input_dim}")
    num_classes = len(set(train_labels))
    model = SmallClassifier(input_dim, output_dim=num_classes)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    train_embeddings_tensor = torch.tensor(train_embeddings, dtype=torch.float32)
    train_labels_tensor = torch.tensor(train_labels, dtype=torch.long)

    for epoch_idx in range(epoch):
        model.train()
        optimizer.zero_grad()
        outputs = model(train_embeddings_tensor)
        loss = criterion(outputs, train_labels_tensor)
        loss.backward()
        optimizer.step()

        print(f'Epoch {epoch_idx + 1}/{epoch}, Loss: {loss.item():.4f}')

    return model


def evaluate_model(model, test_embeddings, test_labels):
    model.eval()
    test_embeddings_tensor = torch.tensor(test_embeddings, dtype=torch.float32)

    with torch.no_grad():
        logits = model(test_embeddings_tensor)
        predictions = torch.argmax(logits, dim=1).tolist()

    average = "binary" if len(set(test_labels)) == 2 else "macro"
    accuracy = accuracy_score(test_labels, predictions)
    f1 = f1_score(test_labels, predictions, average=average)
    return accuracy, f1

def save_model(model, file_path):
    torch.save(model.state_dict(), file_path)

def load_model(file_path, input_dim, hidden_dim=24, output_dim=2):
    model = SmallClassifier(input_dim, hidden_dim, output_dim)
    model.load_state_dict(torch.load(file_path, map_location="cpu"))
    model.eval()
    return model

def encode_text(text):
    embedding = get_sbert_model().encode([text], convert_to_numpy=True)
    return torch.tensor(embedding, dtype=torch.float32)

def predict_from_embedding(embedding_tensor, model):
    model.eval()
    with torch.inference_mode():
        logits = model(embedding_tensor)
        prediction = torch.argmax(logits, dim=1).item()
    return prediction

def run_inference(text, model):
    embedding_tensor = encode_text(text)
    return predict_from_embedding(embedding_tensor, model)

if __name__ == "__main__":
    train_data, test_data = prepare_data('data/ib_dataset.csv')
    print(len(train_data), len(test_data))
    train_embeddings, train_labels, test_embeddings, test_labels = vectorize_data(train_data, test_data)
    model_ib = train_model(train_embeddings, train_labels, epoch=100)
    ib_accuracy, ib_f1 = evaluate_model(model_ib, test_embeddings, test_labels)
    print(f"IB Test Accuracy: {ib_accuracy:.4f} | IB Test F1: {ib_f1:.4f}")

    train_data, test_data = prepare_data('data/ic_dataset.csv')
    train_embeddings, train_labels, test_embeddings, test_labels = vectorize_data(train_data, test_data)
    model_ic = train_model(train_embeddings, train_labels, epoch=100)
    ic_accuracy, ic_f1 = evaluate_model(model_ic, test_embeddings, test_labels)
    print(f"IC Test Accuracy: {ic_accuracy:.4f} | IC Test F1: {ic_f1:.4f}")
    
    save_model(model_ib, 'model/ib_classifier.pth')
    save_model(model_ic, 'model/ic_classifier.pth')   