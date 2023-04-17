# json_converter.py
import json
import re
import settings


def user_message_to_json(entry):
    data = {
        'user_name': entry.user_name,
        'user_message': entry.user_message
    }

    # 'ai_id': entry.ai_id,
    # 'ai_name': entry.ai_name

    return data


def ai_message_to_json(entry):
    data = {
        'ai_id': entry.ai_id,
        'ai_name': entry.ai_name,
        'thoughts': entry.thoughts,
        'to_user': entry.to_user
    }

    if entry.commands is not None and entry.commands != 'null':
        data['commands'] = entry.commands

    return data


def ai_message_to_json_values(ai_id, ai_name, thoughts, to_user, commands):
    data = {
        'ai_id': ai_id,
        'ai_name': ai_name,
        'thoughts': thoughts,
        'to_user': to_user
    }

    if commands is not None and commands != 'null':
        data['commands'] = commands

    return data


def environment_message_to_json(entry):
    data = {
        'ai_id': entry.ai_id,
        'ai_name': entry.ai_name
    }

    if entry.commands is not None and entry.commands != 'null':
        data['commands'] = entry.commands

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

# Convert messages 'content' to string:


def convert_content_to_string(messages):
    messages_with_format = messages.copy()
    for i, message in enumerate(messages_with_format):
        if i == 0 and message['role'] == 'system':
            continue

        content = message['content']
        if isinstance(content, dict):
            message['content'] = json.dumps(content)
    return messages_with_format
