# model.py
import json
import openai
import settings
import tiktoken
import format
import secure_information
import database
import json_converter
import memory
import commands as cmd
from main import app


def model_say_to_model(messages, experience_space, memory_index, metadata, diagnostic=False):
    response, response_message = generate_response(
        messages=messages,
        experience_space=experience_space,
        memory_index=memory_index,
        metadata=metadata,
        diagnostic=diagnostic)

    return response, response_message


def user_say_to_model(user_name,
                      user_message,
                      messages,
                      experience_space,
                      memory_index,
                      metadata,
                      ai_id=secure_information.AI_ID,
                      ai_name=secure_information.AI_NAME,
                      diagnostic=False):

    # Save user message with related AI memories to db
    user_message_id, date_time = save_user_message_with_related_memories_to_db(messages=messages,
                                                                               memory_index=memory_index,
                                                                               metadata=metadata,
                                                                               user_name=user_name,
                                                                               user_message=user_message,
                                                                               experience_space=experience_space,
                                                                               ai_id=ai_id,
                                                                               ai_name=ai_name,
                                                                               diagnostic=diagnostic)

    date_time_str = date_time.strftime(settings.DATE_TIME_FORMAT)

    # Important - model currently will not see apended memories - I need to append them.
    # One more time get all messages using get_context_messages_with_manifest()?

    # Combine user name and user message into a single string
    full_response = {'message_id': user_message_id, 'user_message': user_message,
                     'user_name': user_name, 'date_time': date_time_str}

    # Save to Long-term memory
    if settings.LONG_MEMORY_ENABLED and not diagnostic:
        memory.add_user_message_to_memory(full_response=full_response,
                                          index=memory_index,
                                          metadata=metadata,
                                          message_id=user_message_id,
                                          date_time_str=date_time_str)

    # messages.append(
    #     {"role": "user", "content": full_response})

    updated_messages, _, _ = get_context_messages_with_manifest(ai_id=ai_id,
                                                                experience_space=experience_space,
                                                                memories_only_for_context=True,
                                                                diagnostic=diagnostic)

    response, response_message = generate_response(
        messages=updated_messages,
        experience_space=experience_space,
        memory_index=memory_index,
        metadata=metadata,
        diagnostic=diagnostic)
    return response, response_message


def generate_response(messages,
                      experience_space,
                      memory_index,
                      metadata,
                      context_tokens_limit=settings.CONTEXT_TOKENS_LIMIT,
                      diagnostic=False):

    # Calculate 2nd time to ensure? - first one in get_context_messages_with_manifest()
    remaining_tokens, messages_with_format = remove_messages_longer_than_context(messages=messages,
                                                                                 context_tokens_limit=context_tokens_limit)

    openai.api_key = secure_information.OPEN_AI_API_KEY

    # Generate response using OpenAI API
    response = openai.ChatCompletion.create(
        model=settings.MODEL_ID,
        messages=messages_with_format,
        max_tokens=remaining_tokens,
        n=1,
        stop=None,
        temperature=0.7,
    )

    # Important: here problem when result not in json
    ai_id, ai_name, thoughts, to_user, commands = json_converter.parse_ai_message(
        response.choices[0].message.content)

    # Here execute commands
    commands_result = ""
    if commands is not None and commands != 'null' and json.loads(commands) != 'null' and settings.COMMANDS_ENABLED:
        commands_result = cmd.parse_command(commands)

    if settings.LONG_MEMORY_ENABLED:
        existing_messages_ids = get_message_ids_from_existing_messages(
            messages)

        # Get relevant memories from DB
        filtered_memories = get_full_memories_from_db(get_memory_text=thoughts,
                                                      index=memory_index,
                                                      metadata=metadata,
                                                      existing_messages_ids=existing_messages_ids)
    else:
        existing_messages_ids = []
        filtered_memories = []

    response_message = json_converter.ai_message_to_json_values(
        ai_id, ai_name, thoughts, to_user, commands, commands_result, filtered_memories, existing_messages_ids)

    # Save AI message to db
    ai_message_id, date_time = database.save_ai_message(
        ai_id, ai_name, thoughts, to_user, commands, commands_result, filtered_memories, experience_space, diagnostic)

    date_time_str = date_time.strftime(settings.DATE_TIME_FORMAT)

    # Save to Long-term memory
    if settings.LONG_MEMORY_ENABLED and not diagnostic:
        memory.add_ai_message_to_memory(data=response_message,
                                        index=memory_index,
                                        metadata=metadata,
                                        message_id=ai_message_id,
                                        date_time_str=date_time_str)

    return response, response_message


def save_user_message_with_related_memories_to_db(messages,
                                                  memory_index,
                                                  metadata,
                                                  user_name,
                                                  user_message,
                                                  experience_space,
                                                  ai_id,
                                                  ai_name,
                                                  diagnostic=False):

    if settings.LONG_MEMORY_ENABLED:
        existing_messages_ids = get_message_ids_from_existing_messages(
            messages)

        get_memory_text = f"{user_name}: {user_message}"

        # Get relevant memories from DB
        filtered_memories = get_full_memories_from_db(get_memory_text=get_memory_text,
                                                      index=memory_index,
                                                      metadata=metadata,
                                                      existing_messages_ids=existing_messages_ids)
    else:
        filtered_memories = []

    # Save to DB
    user_message_id, date_time = database.save_user_message(
        user_name, user_message, ai_id, ai_name, experience_space, filtered_memories, diagnostic)

    return user_message_id, date_time

# Leaves messages that fall into model context


def remove_messages_longer_than_context(messages, context_tokens_limit):

    messages_with_format = json_converter.convert_content_to_string(messages)

    # Remove earliest messages until the total tokens are under the limit (except 'system' message)
    while num_tokens_from_messages(messages_with_format) > context_tokens_limit:
        index_to_remove = 1
        messages_with_format.pop(index_to_remove)
        messages.pop(index_to_remove)

    print("messages number in AI context: ", len(messages_with_format))

    # Calculate the remaining tokens for the response
    remaining_tokens = settings.MAX_TOKENS - \
        num_tokens_from_messages(messages_with_format)

    return remaining_tokens, messages_with_format


def get_message_ids_from_existing_messages(existing_messages):
    message_ids = set()

    for message in existing_messages:
        role = message.get('role')
        content_str = message.get('content', '{}')

        if (role == 'system'):
            continue

        try:
            content = json.loads(content_str)
        except json.JSONDecodeError:
            content = {}

        if role == 'assistant' or role == 'user':
            message_id = content.get('message_id')
            if message_id is not None:
                message_ids.add(message_id)

            for memory in content.get('memories', []):
                memory_id = memory.get('message_id')
                if memory_id is not None:
                    message_ids.add(memory_id)

    return message_ids


def get_full_memories_from_db(get_memory_text, index, metadata, existing_messages_ids):
    all_memories = memory.retrieve_relevant_memories(get_memory_text=get_memory_text,
                                                     index=index,
                                                     metadata=metadata)

    # Filter out memories with IDs that already exist in existing_message_ids
    filtered_memories = [
        memory for memory in all_memories if memory['message_id'] not in existing_messages_ids]

    memory_message_ids = [memory['message_id'] for memory in filtered_memories]
    memories = database.get_messages_by_ids(
        memory_message_ids)

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


def get_context_messages_from_db(ai_id,
                                 experience_space,
                                 memories_for_all_messages=False,
                                 messages_number=settings.MESSAGES_LIMIT_FROM_DB,
                                 messages_with_memory_showed_to_ai=settings.MESSAGES_WITH_MEMORY_SHOWED_TO_AI,
                                 diagnostic=False):
    entries = database.get_latest_messages(
        ai_id, experience_space, messages_number, diagnostic)

    messages = []
    ai_name = ""
    entry_count = 0
    total_entries = len(entries)

    if not settings.LONG_MEMORY_ENABLED:
        messages_with_memory_showed_to_ai = 0

    for entry in entries:
        if not ai_name and entry.message_type == "assistant":
            ai_name = entry.ai_name

        if not memories_for_all_messages:
            entry_count += 1
        else:
            entry_count = total_entries

        with_memory = total_entries - entry_count < messages_with_memory_showed_to_ai

        if entry.message_type == "user":
            content = json_converter.user_message_to_json(
                entry, with_memory, diagnostic)
        elif entry.message_type == "assistant":
            content = json_converter.ai_message_to_json(
                entry, with_memory, diagnostic)
        else:
            continue

        messages.append(put_to_open_ai_format(entry.message_type, content))

    if not ai_name:
        ai_name = secure_information.AI_NAME

    return messages, ai_id, ai_name


def get_context_messages_with_manifest(ai_id,
                                       experience_space,
                                       memories_for_all_messages=False,
                                       memories_only_for_context=False,
                                       messages_with_memory_showed_to_ai=settings.MESSAGES_WITH_MEMORY_SHOWED_TO_AI,
                                       diagnostic=False):

    messages = create_manifest_message()
    messages_from_db, ai_id, ai_name = get_context_messages_from_db(
        ai_id=ai_id,
        experience_space=experience_space,
        memories_for_all_messages=memories_for_all_messages,
        messages_with_memory_showed_to_ai=messages_with_memory_showed_to_ai,
        diagnostic=diagnostic)

    messages.extend(messages_from_db)

    if memories_only_for_context:
        remaining_tokens, messages_with_format = remove_messages_longer_than_context(messages=messages,
                                                                                     context_tokens_limit=settings.CONTEXT_TOKENS_LIMIT)

    return messages, ai_id, ai_name


# Create OpenAI format message
def put_to_open_ai_format(message_type, content):
    data = {"role": message_type, "content": content}
    return data

# Manifest message


def create_manifest_message():
    plans_str = get_current_plan()

    return [
        {'role': 'system', 'content': format.MANIFEST.format(
            user_name=secure_information.USER_NAME,
            ai_id=secure_information.AI_ID,
            ai_name=secure_information.AI_NAME,
            plans=plans_str,
            root_path=app.root_path)}
    ]


def get_current_plan():
    plans_list = database.get_all_plans()
    plans_str = "\n".join(plans_list)

    return plans_str
