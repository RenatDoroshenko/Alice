import json
import code_execution_commands as code_cmd
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
    "get_text": get_text,

    # File commands
    "read_file": code_cmd.read_file,
    "write_file": code_cmd.write_file,
    "delete_file": code_cmd.delete_file,
    "insert_lines": code_cmd.insert_lines,
    "delete_lines": code_cmd.delete_lines,
    "execute_file": code_cmd.execute_file,
    "list_files": code_cmd.list_files,

    # File commands in App
    "list_directory_in_app": code_cmd.list_directory_in_app,
    "read_file_in_app": code_cmd.read_file_in_app,

    # Command line
    "run_command": code_cmd.run_command
}


def parse_command(commands_str):
    command_results = []

    print(f"Start parsing commands: {commands_str}")

    commands = json.loads(commands_str)
    if commands is None or commands == 'null':
        print(f"Wrong format of commands: {commands}")
        return ""

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
