import time
import openai
import faiss
import numpy as np
import json
import os
import settings
import secure_information
import nltk
from datetime import datetime

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt")


# Replace this with your OpenAI API key
openai.api_key = secure_information.OPEN_AI_API_KEY

# Function to get embeddings from OpenAI API


def get_embeddings(sentences, max_retries=3, delay=1):
    retries = 0
    while retries < max_retries:
        try:
            response = openai.Embedding.create(
                model=settings.EMBEDDING_MODEL,
                input=sentences
            )
            embeddings = [result["embedding"] for result in response["data"]]
            return np.array(embeddings)
        except openai.error.APIError as e:
            print(f"Error in get_embeddings: {e}")
            retries += 1
            if retries < max_retries:
                print(f"Retrying... (attempt {retries})")
                time.sleep(delay)
            else:
                print("Max retries reached. Raising the exception.")
                raise e


# Using shards


def add_user_message_to_memory(full_response, index, metadata, message_id):
    user_name = full_response.get('user_name')
    user_message = full_response.get('user_message')

    if not user_name or not user_message:
        print("add_user_message_to_memory - full_response: " + full_response)
        raise ValueError("User name and message must be provided.")

    user_sentences = nltk.sent_tokenize(user_message)
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    for sentence in user_sentences:
        text = f"{current_datetime}, {user_name}: {sentence}"
        add_response_to_memory(sentence=text,
                               index=index,
                               metadata=metadata,
                               message_id=message_id)


def add_ai_message_to_memory(data, index, metadata, message_id):
    ai_id = data.get('ai_id')
    ai_name = data.get('ai_name')
    thoughts = data.get('thoughts', '')
    to_user = data.get('to_user', '')
    commands = data.get('commands', '')

    if not ai_id or not ai_name:
        print('add_ai_message_to_memory - data: ' + data)
        raise ValueError("AI id and name must be provided.")

    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if thoughts:
        thoughts_sentences = nltk.sent_tokenize(thoughts)
        for sentence in thoughts_sentences:
            text = f"{current_datetime}, {ai_name}-{ai_id} thoughts: {sentence}"
            add_response_to_memory(sentence=text,
                                   index=index,
                                   metadata=metadata,
                                   message_id=message_id)

    if to_user:
        to_user_sentences = nltk.sent_tokenize(to_user)
        for sentence in to_user_sentences:
            text = f"{current_datetime}, {ai_name}-{ai_id} says to user: {sentence}"
            add_response_to_memory(sentence=text,
                                   index=index,
                                   metadata=metadata,
                                   message_id=message_id)
    if commands:
        commands_sentences = nltk.sent_tokenize(commands)
        for sentence in commands_sentences:
            text = f"{current_datetime}, {ai_name}-{ai_id} commands: {sentence}"
            add_response_to_memory(sentence=text,
                                   index=index,
                                   metadata=metadata,
                                   message_id=message_id)


def add_response_to_memory(sentence, index, metadata, message_id):
    embedding = get_embeddings(sentence)
    print('embedding: ', embedding)
    print('embedding after reshape: ', embedding.reshape(1, -1))
    print('message_id: ', message_id)
    index.add_with_ids(embedding.reshape(1, -1), np.array([message_id]))
    metadata.append({"message_id": message_id, "sentence": sentence})


def retrieve_relevant_memories(index, metadata, thoughts, k=3):
    # k - Number of closest embeddings to return - associative memory
    thought_embeddings = get_embeddings([thoughts])
    distances, indices = index.search(thought_embeddings.reshape(1, -1), k)

    relevant_memories = []
    for idx in indices[0]:
        relevant_memories.append(metadata[idx])

    return relevant_memories


def is_index_in_collection(collection, index):
    for i in range(collection.count()):
        if collection.at(i) == index:
            return True
    return False


def initialize_faiss_index(dimension=settings.VECTOR_INDEX_DIMENSION, folder_path=settings.FAISS_INDEX_FOLDER):
    index_file = os.path.join(folder_path, "faiss_index.bin")

    if os.path.exists(index_file):
        index = faiss.read_index(index_file)
    else:
        index_flat_l2 = faiss.IndexFlatL2(dimension)
        index = faiss.IndexIDMap(index_flat_l2)

    return index


def load_memory_index(folder_path=settings.FAISS_INDEX_FOLDER):
    index = initialize_faiss_index()

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

    index_file = os.path.join(folder_path, "faiss_index.bin")
    faiss.write_index(index, index_file)

    metadata_path = os.path.join(folder_path, "metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f)
