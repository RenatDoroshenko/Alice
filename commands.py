import json
# FORMAT:

# "commands": [
#     {
#         "name": "show_details",
#         "parameters": {
#             "id": 1234,
#             "detail_level": "high"
#         }
#     },
#     {
#         "name": "send_email",
#         "parameters": {
#             "recipient": "someone@example.com",
#             "subject": "Hello",
#             "body": "This is a test email."
#         }
#     }
#     // Add more commands here
# ]


# Commands Definition


def print_text(text):

    # Log message
    print(f'Executing print_text with text={text}')

    return "print_text command executed successfully"


def get_text():
    text = "Sparks of AGI"
    return text


# Register Commands
registered_commands = {
    "print_text": print_text,
    'get_text': get_text
}


def parse_command(commands_str):
    command_results = []

    print(f"Start parsing commands: {commands_str}")

    commands = json.loads(commands_str)

    for command_data in commands:
        command_name = command_data['name']
        print(f"command_name: {command_name}")

        parameters = command_data.get('parameters', {})
        print(f"parameters: {parameters}")

        # Look up the command function
        command_func = registered_commands.get(command_name)
        if command_func:
            # Execute the command function with the parameters and get the result
            result = command_func(**parameters)
            command_result = {
                "command": command_name,
                "result": result,
            }
            print(f"{command_name} command result: {command_result}")

            command_results.append(command_result)
        else:
            print(f'Unknown command: {command_name}')

    return command_results
