# json_converter.py
import json.decoder
import json
import re
import settings
from datetime import datetime


# For memory entries only


def convert_db_memories_messages_to_json(entries):
    messages = []

    for entry in entries:
        if entry.message_type == "user":
            content = user_message_to_json(entry)

        elif entry.message_type == "assistant":
            content = ai_message_to_json(entry, withMemory=False)
        else:
            continue

        messages.append(content)

    return messages


def user_message_to_json(entry):
    data = {
        'message_id': entry.id,
        'user_name': entry.user_name,
        'user_message': entry.user_message,
        'date_time': entry.date_time.strftime(settings.DATE_TIME_FORMAT)
    }

    # 'ai_id': entry.ai_id,
    # 'ai_name': entry.ai_name

    return data


def ai_message_to_json(entry, withMemory=True):
    data = {
        'message_id': entry.id,
        'ai_id': entry.ai_id,
        'ai_name': entry.ai_name,
        'thoughts': entry.thoughts,
        'to_user': entry.to_user,
        'date_time': entry.date_time.strftime(settings.DATE_TIME_FORMAT)
    }

    if entry.commands is not None and entry.commands != 'null':
        data['commands'] = json.loads(entry.commands)

    if withMemory:
        if entry.memories is not None and entry.memories != 'null':
            # Here is format of messages from db
            memories = json.loads(entry.memories)
            if len(memories) != 0:
                formatted_memories = convert_db_memories_messages_to_json_from_dict(
                    memories)
                data['memories'] = formatted_memories

    return data


def convert_db_memories_messages_to_json_from_dict(entries):
    messages = []
    for entry in entries:
        if entry['message_type'] == "user":
            content = user_message_to_json_from_dict(entry)

        elif entry['message_type'] == "assistant":
            content = ai_message_to_json_from_dict(entry, withMemory=False)
        else:
            continue

        messages.append(content)

    return messages


def user_message_to_json_from_dict(entry):
    # print('user_message_to_json_from_dict - entry', entry)

    date_time = datetime.fromisoformat(entry['date_time'])

    data = {
        'message_id': entry['id'],
        'user_name': entry['user_name'],
        'user_message': entry['user_message'],
        'date_time': date_time.strftime(settings.DATE_TIME_FORMAT)
    }

    # 'ai_id': entry.ai_id,
    # 'ai_name': entry.ai_name

    return data


def ai_message_to_json_from_dict(entry, withMemory=True):

    date_time = datetime.fromisoformat(entry['date_time'])

    data = {
        'message_id': entry['id'],
        'ai_id': entry['ai_id'],
        'ai_name': entry['ai_name'],
        'thoughts': entry['thoughts'],
        'to_user': entry['to_user'],
        'date_time': date_time.strftime(settings.DATE_TIME_FORMAT)
    }

    if entry['commands'] is not None and entry['commands'] != 'null':
        data['commands'] = json.loads(entry['commands'])

    if withMemory:
        if entry['memories'] is not None and entry['memories'] != 'null':
            # Here is format of messages from db
            memories = json.loads(entry['memories'])
            if len(memories) != 0:
                formatted_memories = convert_db_memories_messages_to_json_from_dict(
                    memories)
                data['memories'] = formatted_memories

    return data


# Used when model responded
def ai_message_to_json_values(ai_id, ai_name, thoughts, to_user, commands, memories):
    data = {
        'ai_id': ai_id,
        'ai_name': ai_name,
        'thoughts': thoughts,
        'to_user': to_user
    }

    if commands is not None and commands != 'null':
        data['commands'] = commands

    if memories:
        formatted_memories = convert_db_memories_messages_to_json(memories)
        data['memories'] = formatted_memories

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


def fix_unclosed_double_quotes(json_data):
    stack = []
    fixed_json_data = ""

    for c in json_data:
        if c == '"':
            if len(stack) > 0 and stack[-1] == '"':
                stack.pop()
            else:
                stack.append(c)
        fixed_json_data += c

        if len(stack) == 1 and (c == ',' or c == ':'):
            fixed_json_data = fixed_json_data[:-1] + '"' + c
            stack.pop()

    if len(stack) == 1:
        fixed_json_data += '"'

    return fixed_json_data


def remove_invalid_control_characters(json_data):
    return ''.join(c for c in json_data if c not in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f')


def ensure_json_format(json_data):
    if not is_valid_json(json_data):
        print("There is an issue with the JSON data. Attempting to fix it...")

        if settings.TERMINAL_LOGS_ENABLED:
            print("Json with issues: ", json_data)

        fixed_json_data = fix_unclosed_double_quotes(json_data)
        fixed_json_data = fix_missing_braces(fixed_json_data)
        fixed_json_data = fix_missing_commas(fixed_json_data)

        if settings.TERMINAL_LOGS_ENABLED:
            print("Fixed json: ", fixed_json_data)

        if is_valid_json(fixed_json_data):
            print("JSON data fixed.")
            json_data = fixed_json_data
        else:
            print("Failed to fix the JSON data.")


def replace_newlines_with_html_br(text):
    return text.replace('\n', '<br>')

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

    # json_data = remove_invalid_control_characters(json_data)
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
