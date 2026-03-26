import csv
import itertools
import random

def generate_ib_data():
    info_topics = ["photosynthesis", "black holes", "the Roman Empire", "machine learning", "quantum physics", "World War II", "DNA replication", "the stock market", "capitalism", "climate change", "the industrial revolution", "Mars", "the human brain", "viruses", "bacteria", "the French Revolution", "the printing press", "the solar system", "the internet", "cryptocurrency", "the Renaissance", "the Cold War", "the history of art", "the origin of water on Earth", "ancient Egypt", "Mayan pyramids", "feudalism", "evolutionary biology", "plate tectonics", "the Big Bang", "the speed of light", "atomic structure"]
    info_templates = ["What is {}", "Explain {}", "How does {} work?", "Tell me about {}", "Give me a summary of {}", "What causes {}", "Who discovered {}", "When did {} start?", "Describe the history of {}", "Why is {} important?", "I need information on {}", "Detail {}"]
    
    task_topics = ["a python script", "an email", "a song", "a rap", "a poem", "a short story", "a business plan", "a resume", "a cover letter", "a marketing strategy", "a C++ compiler", "a React component", "a backend server", "a SQL query", "a presentation", "to jump", "a novel", "a character in a game", "a shader", "a spreadsheet", "a bash script", "a recipe for lasagna", "a travel itinerary", "a workout plan", "a user manual", "a budget planner", "an API design", "a database schema"]
    task_templates = ["Write {}", "Generate {}", "Create {}", "Draft {}", "Compose {}", "Make {}", "Can you program {}", "Build {}", "Formulate {}", "Develop {}"]

    data = []
    for topic, template in itertools.product(info_topics, info_templates):
        data.append((template.format(topic), 0))
    for topic, template in itertools.product(task_topics, task_templates):
        data.append((template.format(topic), 1))
        
    random.shuffle(data)
    return data

def generate_ic_data():
    low_complex_topics = ["what is 2+2", "capital of France", "hello", "good morning", "is the sky blue", "who is the president", "how many continents are there", "days in a week", "what is a dog", "who wrote romeo and juliet", "when is christmas", "is water wet", "how many hours in a day", "what does the fox say", "basic math", "simple addition", "color of grass", "name a fruit", "what is a cat"]
    low_complex_templates = ["{}", "tell me: {}", "can you answer {}", "I want to know {}", "please say {}"]

    high_complex_topics = ["a multithreaded web server in Rust", "the socioeconomic impact of AI on global supply chains", "a 3D graphics rendering engine from scratch", "the mathematical proof of Fermat's Last Theorem", "a comprehensive comparative analysis between Kant and Hegel", "a full compiler in C", "the architecture of a scalable microservices backend", "a custom neural network framework", "an operating system kernel", "a fully featured distributed database system", "the political climate during the fall of the Byzantine Empire", "a novel cryptographic hashing algorithm", "a decentralized blockchain consensus protocol", "the physics of a warp drive"]
    high_complex_templates = ["Explain in deep detail {}", "Write {}", "Design {}", "Can you fully implement {}", "Draft an expert essay on {}", "Provide a comprehensive guide to {}", "Show me the full math behind {}"]

    data = []
    for topic, template in itertools.product(low_complex_topics, low_complex_templates):
        data.append((template.format(topic), 0))
    for topic, template in itertools.product(high_complex_topics, high_complex_templates):
        data.append((template.format(topic), 1))
        
    random.shuffle(data)
    return data

def append_to_csv(filename, data):
    with open(filename, 'a', newline='') as f:
        writer = csv.writer(f)
        for row in data:
            writer.writerow(row)

ib = generate_ib_data()
ic = generate_ic_data()
append_to_csv('ib_dataset.csv', ib)
append_to_csv('ic_dataset.csv', ic)

print(f"Added {len(ib)} standard IB items and {len(ic)} standard IC items.")