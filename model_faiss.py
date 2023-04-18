import openai
import faiss
import numpy as np
import nltk
import json
import os
import settings
import secure_information

# Replace this with your OpenAI API key
openai.api_key = secure_information.OPEN_AI_API_KEY

# Function to get embeddings from OpenAI API


def get_embeddings(sentences):
    response = openai.Embedding.create(
        model=settings.EMBEDDING_MODEL,
        input=sentences
    )
    embeddings = [result["embedding"] for result in response["data"]]
    return np.array(embeddings)

# Using shards


def add_response_to_memory(index, metadata, response, message_id):
    sentences = nltk.sent_tokenize(response)
    sentence_embeddings = get_embeddings(sentences)

    for i, embedding in enumerate(sentence_embeddings):
        index.add_with_ids(embedding.reshape(1, -1), np.array([message_id]))
        metadata.append({"message_id": message_id, "sentence_index": i})


def retrieve_relevant_memories(index, metadata, thoughts, k=3):
    # k - Number of closest embeddings to return - associative memory
    thought_embeddings = get_embeddings([thoughts])
    distances, indices = index.search(thought_embeddings.reshape(1, -1), k)

    relevant_memories = []
    for idx in indices[0]:
        relevant_memories.append(metadata[idx])

    return relevant_memories


def initialize_faiss_index(dimension=settings.VECTOR_INDEX_DIMENSION, n_shards=4):
    index = faiss.IndexShards(dimension)
    for _ in range(n_shards):
        sub_index = faiss.IndexFlatL2(dimension)
        index.add_index(sub_index)
    return index


def load_memory_index(folder_path=settings.FAISS_INDEX_FOLDER, n_shards=4):
    index = initialize_faiss_index(n_shards=n_shards)

    for shard_id in range(n_shards):
        shard_file = os.path.join(
            folder_path, f"faiss_index_shard_{shard_id}.bin")

        if os.path.exists(shard_file):
            index.at(shard_id).read(shard_file)

    metadata_path = os.path.join(folder_path, "metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
    else:
        metadata = []

    return index, metadata


def save_memory_index(index, metadata, folder_path=settings.FAISS_INDEX_FOLDER):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    n_shards = index.count()
    for shard_id in range(n_shards):
        shard_file = os.path.join(
            folder_path, f"faiss_index_shard_{shard_id}.bin")
        index.at(shard_id).write(shard_file)

    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)


# Save and load from file (always overwrite)
# def add_response_to_memory(index, response, metadata):
#     sentences = nltk.sent_tokenize(response)
#     embeddings = get_embeddings(sentences)
#     index.add_with_ids(embeddings.astype('float32'),
#                        np.array(range(len(sentences))))
#     return metadata + [{'message_id': len(metadata) + i, 'timestamp': '2023-04-18 10:30:00'} for i in range(len(sentences))]


# def retrieve_relevant_memories(index, metadata, thoughts, k=3):
#     thought_embeddings = get_embeddings([thoughts])
#     distances, indices = index.search(thought_embeddings.astype('float32'), k)

#     relevant_memories = []
#     for i in range(k):
#         memory_metadata = metadata[indices[0][i]]
#         relevant_memories.append(memory_metadata)

#     return relevant_memories

# def save_memory_index(index, metadata, folder_path=settings.FAISS_INDEX_FOLDER):
#     # Create the memory folder if it doesn't exist
#     os.makedirs(folder_path, exist_ok=True)

#     # Save the index
#     index_path = os.path.join(folder_path, "faiss_index.bin")
#     faiss.write_index(index, index_path)

#     # Save the metadata
#     metadata_path = os.path.join(folder_path, "metadata.json")
#     with open(metadata_path, "w") as f:
#         json.dump(metadata, f)


# def load_memory_index(folder_path=settings.FAISS_INDEX_FOLDER):
#     # Check if the memory folder exists
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path)
#         index = faiss.IndexFlatL2(settings.VECTOR_INDEX_DIMENSION)
#         metadata = []
#     else:
#         try:
#             # Load the index
#             index_path = os.path.join(folder_path, "faiss_index.bin")
#             index = faiss.read_index(index_path)

#             # Load the metadata
#             metadata_path = os.path.join(folder_path, "metadata.json")
#             with open(metadata_path, "r") as f:
#                 metadata = json.load(f)
#         except (FileNotFoundError, IOError):
#             # Create a new index and metadata if the files are not found
#             index = faiss.IndexFlatL2(settings.VECTOR_INDEX_DIMENSION)
#             metadata = []

#     return index, metadata

# def initialize_faiss_index(embedding_dim):
#     index = faiss.IndexFlatL2(embedding_dim)
#     return index


# Example usage:

# # Add a response to memory
# response = "Your response text here."
# metadata = []
# metadata = add_response_to_memory(index, response, metadata)

# # Retrieve relevant memories based on the model's thoughts
# thoughts = "Thoughts text here."
# relevant_memories = retrieve_relevant_memories(index, metadata, thoughts)
