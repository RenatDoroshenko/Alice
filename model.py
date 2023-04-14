# model.py
import json
import openai
import settings
import tiktoken
import format
import secure_information
import database
import re


def model_say_to_model(messages, experience_space):

    response = generate_response(messages, experience_space)
    return response


def user_say_to_model(user_name, user_message, messages, experience_space, ai_id=secure_information.AI_ID, ai_name=secure_information.AI_NAME):

    if settings.SAVE_TO_DB:
        database.save_user_message(
            user_name, user_message, ai_id, ai_name, experience_space)

    full_response = format.USER_RESPONSE.format(
        user_name=user_name, content=user_message)
    messages.append(
        {"role": "user", "content": full_response})
    response = generate_response(messages, experience_space)
    return response


def generate_response(messages, experience_space, context_tokens_limit=settings.CONTEXT_TOKENS_LIMIT):
    openai.api_key = secure_information.OPEN_AI_API_KEY

    # Remove earliest messages until the total tokens are under the limit (except 'system' message)
    while num_tokens_from_messages(messages) > context_tokens_limit:
        messages.pop(1)

    # Combine messages into a single string
    # prompt = "\n\n".join(
    #     [f"{msg['role'].title()}: {msg['content']}" for msg in messages]) + "\n\n"

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

    if settings.SAVE_TO_DB:
        # Important: here problem when result not in json
        ai_id, ai_name, thoughts, to_user, commands = parse_ai_message(
            response.choices[0].message.content)

    if settings.SAVE_TO_DB:
        database.save_ai_message(
            ai_id, ai_name, thoughts, to_user, commands, experience_space)

    return response


def chatgpt_conversation(messages, role):
    response = openai.ChatCompletion.create(
        model=settings.MODEL_ID,
        messages=messages
    )
    messages.append({
        "role": role, "content": response.choices[0].message.content
    })

    return messages


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
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens

# Parse JSON


def parse_user_message(json_data):
    # if settings.TERMINAL_LOGS_ENABLED:
    #     print("User message to save: ", json_data)

    ensure_json_format(json_data)

    data = json.loads(json_data)
    user_name = data.get('user_name')
    user_message = data.get('user_message')
    ai_id = int(data.get('ai_id')) if data.get('ai_id') is not None else None
    ai_name = data.get('ai_name')
    return user_name, user_message, ai_id, ai_name


def parse_ai_message(json_data):
    # if settings.TERMINAL_LOGS_ENABLED:
    #     print("AI message to save: ", json_data)

    ensure_json_format(json_data)

    data = json.loads(json_data)
    ai_id = int(data.get('ai_id')) if data.get('ai_id') is not None else None
    ai_name = data.get('ai_name')
    thoughts = data.get('thoughts')
    to_user = data.get('to_user')
    commands = json.dumps(data.get('commands'))
    return ai_id, ai_name, thoughts, to_user, commands


def parse_environment_message(json_data):
    # if settings.TERMINAL_LOGS_ENABLED:
    #     print("Environment message to save: ", json_data)

    ensure_json_format(json_data)

    data = json.loads(json_data)
    ai_id = int(data.get('ai_id')) if data.get('ai_id') is not None else None
    ai_name = data.get('ai_name')
    commands = json.dumps(data.get('commands'))
    return ai_id, ai_name, commands

# Convert to JSON


def get_context_messages_from_db(ai_id=secure_information.AI_ID, experience_space=settings.DEFAULT_EXPERIENCE_SPACE):
    entries = database.get_latest_messages(ai_id, experience_space)

    messages = []

    for entry in entries:

        if entry.message_type == "user":
            content = user_message_to_json(entry)

        elif entry.message_type == "assistant":
            content = ai_message_to_json(entry)
        else:
            continue

        messages.append(put_to_open_ai_format(entry.message_type, content))

    return messages


def user_message_to_json(entry):
    data = {
        'user_name': entry.user_name,
        'user_message': entry.user_message,
        'ai_id': entry.ai_id,
        'ai_name': entry.ai_name
    }
    return data


def ai_message_to_json(entry):
    data = {
        'ai_id': entry.ai_id,
        'ai_name': entry.ai_name,
        'thoughts': entry.thoughts,
        'to_user': entry.to_user,
        'commands': entry.commands
    }
    return data


def environment_message_to_json(ai_id, ai_name, commands):
    data = {
        'ai_id': ai_id,
        'ai_name': ai_name,
        'commands': commands
    }
    return data

# Create OpenAI format message


def put_to_open_ai_format(message_type, content):
    data = {"role": message_type, "content": content}
    return data


# Detect when AI forget to add brackets to json

def is_valid_json(json_data):
    try:
        json.loads(json_data)
        return True
    except json.JSONDecodeError:
        return False


def fix_missing_braces(json_data):
    opening_braces = json_data.count('{')
    closing_braces = json_data.count('}')

    if opening_braces > closing_braces:
        missing_braces = opening_braces - closing_braces
        json_data += '}' * missing_braces

    return json_data


def fix_missing_commas(json_data):
    json_data = re.sub(r'(?<=")(\s*\n\s*)"(?=\w+)', r',\1"', json_data)
    return json_data


def ensure_json_format(json_data):
    if not is_valid_json(json_data):
        print("There is an issue with the JSON data. Attempting to fix it...")

        if settings.TERMINAL_LOGS_ENABLED:
            print("Json with issues: ", json_data)

        fixed_json_data = fix_missing_braces(json_data)
        fixed_json_data = fix_missing_commas(fixed_json_data)

        if settings.TERMINAL_LOGS_ENABLED:
            print("Fixed json: ", json_data)

        if is_valid_json(fixed_json_data):
            print("JSON data fixed.")
            json_data = fixed_json_data
        else:
            print("Failed to fix the JSON data.")


# Manifest message
def create_manifest_message():
    return [
        {'role': 'system', 'content': format.MANIFEST.format(
            user_name=secure_information.USER_NAME, ai_id=secure_information.AI_ID, ai_name=secure_information.AI_NAME)}
    ]
