import csv
from typing import Literal

def build_dataset(input_data:list, output_file):
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['text', 'label']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for text, label in input_data:
            writer.writerow({'text': text, 'label': label})

def read_dataset(input_file):
    dataset = []
    with open(input_file, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dataset.append((row['text'], row['label']))
    return dataset

def split_dataset(dataset, train_ratio=0.8):
    train_size = int(len(dataset) * train_ratio)
    train_data = dataset[:train_size]
    test_data = dataset[train_size:]
    return train_data, test_data

def form_dataset(type:Literal["information-based", "information-complexity"] = "information-based"):
    output = []
    while True:
        try:
            query = input("Enter a query (or '//exit' to finish): ")
            if query == '//exit':
                break
            label = input("Enter the label for this query (0: information-based, 1: task-based): ") if type == "information-based" else input("Enter the label for this query (0: low-complexity, 1: high-complexity): ")
            if label not in ['0', '1']:
                print("Invalid label. Please enter 0 or 1.")
                continue
            output.append((query, label))
        except KeyboardInterrupt:
            print("\nExiting dataset formation.")
            break
    return output

def _main():
    dataset = form_dataset('information-based')
    output_file = 'ib_dataset.csv'
    build_dataset(dataset, output_file)
    print(f"Dataset saved to {output_file}")
    datset = form_dataset('information-complexity')
    output_file = 'ic_dataset.csv'
    build_dataset(datset, output_file)
    print(f"Dataset saved to {output_file}")

if __name__ == "__main__":
    _main()