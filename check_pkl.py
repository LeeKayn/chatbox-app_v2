import pickle
import os

file_path = 'knowledge_graph.pkl'  # Change this to your actual file path

# Check if the file exists before loading
if os.path.exists(file_path):
    try:
        # Load the knowledge graph from the file
        with open(file_path, 'rb') as file:
            kg_loaded = pickle.load(file)
        print(f"[INFO] Knowledge graph loaded successfully from {file_path}")
        print(kg_loaded)
    except (pickle.UnpicklingError, EOFError) as e:
        print(f"[ERROR] Failed to load the knowledge graph: {e}")
else:
    print(f"[ERROR] The file {file_path} does not exist.")
