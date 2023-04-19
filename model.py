# model.py
import openai
import settings
import tiktoken
import format
import secure_information
import database
import json_converter
import memory


def model_say_to_model(messages, experience_space, memory_index, metadata):

    messages_with_format = json_converter.convert_content_to_string(messages)
    response, response_message = generate_response(
        messages=messages_with_format,
        experience_space=experience_space,
        memory_index=memory_index,
        metadata=metadata)

    return response, response_message


def user_say_to_model(user_name, user_message, messages, experience_space, memory_index, metadata, ai_id=secure_information.AI_ID, ai_name=secure_information.AI_NAME):

    # Combine user name and user message into a single string
    full_response = {'user_message': user_message, 'user_name': user_name}

    # Save to DB
    user_message_id = database.save_user_message(
        user_name, user_message, ai_id, ai_name, experience_space)

    # Save to Long-term memory
    memory.add_user_message_to_memory(full_response,
                                      memory_index, metadata, user_message_id)

    messages.append(
        {"role": "user", "content": full_response})

    messages_with_format = json_converter.convert_content_to_string(messages)

    response, response_message = generate_response(
        messages=messages_with_format,
        experience_space=experience_space,
        memory_index=memory_index,
        metadata=metadata)
    return response, response_message


def generate_response(messages, experience_space, memory_index, metadata, context_tokens_limit=settings.CONTEXT_TOKENS_LIMIT):
    openai.api_key = secure_information.OPEN_AI_API_KEY

    # Remove earliest messages until the total tokens are under the limit (except 'system' message)
    while num_tokens_from_messages(messages) > context_tokens_limit:
        messages.pop(1)

    # Calculate the remaining tokens for the response
    remaining_tokens = settings.MAX_TOKENS - num_tokens_from_messages(messages)

    # Generate response using OpenAI API
    response = openai.ChatCompletion.create(
        model=settings.MODEL_ID,
        messages=messages,
        max_tokens=remaining_tokens,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Important: here problem when result not in json
    ai_id, ai_name, thoughts, to_user, commands = json_converter.parse_ai_message(
        response.choices[0].message.content)

    # Get relevant memories from DB
    memories = get_full_memories_from_db(thoughts=thoughts,
                                         index=memory_index,
                                         metadata=metadata)

    response_message = json_converter.ai_message_to_json_values(
        ai_id, ai_name, thoughts, to_user, commands, memories)

    # Save AI message to db
    ai_message_id = database.save_ai_message(
        ai_id, ai_name, thoughts, to_user, commands, memories, experience_space)

    # Save to Long-term memory
    memory.add_ai_message_to_memory(response_message,
                                    memory_index, metadata, ai_message_id)

    return response, response_message


def get_full_memories_from_db(thoughts, index, metadata):
    memories = memory.retrieve_relevant_memories(thoughts=thoughts,
                                                 index=index,
                                                 metadata=metadata)

    memory_message_ids = [memory['message_id'] for memory in memories]
    memories = database.get_messages_by_ids(memory_message_ids)

    return memories


def create_test_messages():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the world series in 2020?"},
        {"role": "assistant",
            "content": "The Los Angeles Dodgers won the World Series in 2020."},
        {"role": "user", "content": "Where was it played?"}
    ]
    return messages


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print(
            "Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_message = 4
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            # Skip counting tokens for ai_id and ai_name keys
            # if key in ["ai_id", "ai_name"]:
            #     continue

            if isinstance(value, dict):
                for sub_value in value.values():
                    if sub_value is not None:
                        num_tokens += len(encoding.encode(sub_value))
            else:
                num_tokens += len(encoding.encode(value))

            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def get_context_messages_from_db(ai_id, experience_space):
    entries = database.get_latest_messages(ai_id, experience_space)

    messages = []
    ai_name = ""

    for entry in entries:

        if entry.message_type == "user":
            content = json_converter.user_message_to_json(entry)

        elif entry.message_type == "assistant":
            if not ai_name:
                ai_name = entry.ai_name
            content = json_converter.ai_message_to_json(entry)
        else:
            continue

        messages.append(put_to_open_ai_format(entry.message_type, content))

    if not ai_name:
        ai_name = secure_information.AI_NAME

    return messages, ai_id, ai_name


def get_context_messages_with_manifest(ai_id, experience_space):
    messages = create_manifest_message()
    messages_from_db, ai_id, ai_name = get_context_messages_from_db(
        ai_id, experience_space)
    messages.extend(messages_from_db)

    return messages, ai_id, ai_name


# Create OpenAI format message
def put_to_open_ai_format(message_type, content):
    data = {"role": message_type, "content": content}
    return data

# Manifest message


def create_manifest_message():
    return [
        {'role': 'system', 'content': format.MANIFEST.format(
            user_name=secure_information.USER_NAME, ai_id=secure_information.AI_ID, ai_name=secure_information.AI_NAME)}
    ]
