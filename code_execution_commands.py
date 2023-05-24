import subprocess
import os
import html
import pandas as pd
import datetime

# The folder where files will be created
folder_path = "model_files"


def list_files():
    print(f'COMMANDS: list_files')
    return os.listdir(folder_path)


def read_file(filename, start_line=0, num_lines=100):
    print(
        f'COMMANDS: read_file - filename={filename}, start_line={start_line}, num_lines={num_lines}')
    lines = []
    total_lines = 0

    # First, count all lines in the file
    with open(f"{folder_path}/{filename}", "r") as f:
        for i, line in enumerate(f):
            total_lines += 1

    # Then, read the specific lines
    with open(f"{folder_path}/{filename}", "r") as f:
        for i, line in enumerate(f):
            if i < start_line:
                continue
            if len(lines) < num_lines:
                # Add line number to line content
                lines.append(f"{i+1}: {line}")
            else:
                break

    # -1 because line numbers are zero-indexed
    end_line = start_line + len(lines) - 1

    return {
        'content': ''.join(lines),
        'total_lines': total_lines,
        'start_line': start_line,
        'end_line': end_line,
    }


def read_command_description_file():
    command_description_content = read_file(
        "data/commands_description.txt", start_line=0, num_lines=1000)
    return command_description_content


def get_api_keys():
    api_keys_content = read_file_in_app("secure_information.py", 0, 1000)
    return api_keys_content


def write_file(filename, content):
    print(f'COMMANDS: create_file - filename={filename}, content={content}')

    with open(f"{folder_path}/{filename}", "w") as f:
        f.write(content)

    return f"Content was written in '{filename}' succesfully."


def delete_file(filename):
    print(f'COMMANDS: delete_file - filename={filename}')
    os.remove(f"{folder_path}/{filename}")

    return f"File '{filename}' was removed succesfully."


def insert_lines(filename, start_line_number, lines_content):
    '''
    Parameters:
    lines_content - list of strings. 

    Example:
    insert_lines("myfile.py", 5, ["line 1", "line 2", "line 3"])

    '''
    print(
        f'COMMANDS: insert_lines - filename={filename}, start_line_number={start_line_number}, lines_content={lines_content}')

    with open(f"{folder_path}/{filename}", "r") as f:
        lines = f.readlines()

    for i, line_content in enumerate(lines_content):
        lines.insert(start_line_number - 1 + i, line_content + "\n")

    with open(f"{folder_path}/{filename}", "w") as f:
        f.writelines(lines)

    return f"Lines were added successfully."


def delete_lines(filename, start_line_number, end_line_number):
    print(
        f'COMMANDS: delete_lines - filename={filename}, start_line_number={start_line_number}, end_line_number={end_line_number}')

    with open(f"{folder_path}/{filename}", "r") as f:
        lines = f.readlines()

    del lines[start_line_number - 1:end_line_number]

    with open(f"{folder_path}/{filename}", "w") as f:
        f.writelines(lines)

    return f"Lines were deleted successfully."


def execute_file(filename):
    python_command = get_python_command()
    print(f'COMMANDS: execute_file - filename={filename}')
    result = subprocess.run(
        [python_command, f"{folder_path}/{filename}"], capture_output=True, text=True)
    return f"Result of '{filename}' execution: {result.stdout}"


def get_python_command():
    for command in ["python3", "python"]:
        try:
            subprocess.check_output([command, "--version"])
            return command
        except Exception:
            pass
    raise RuntimeError("No Python interpreter found")

# All Project


def list_directory_in_app(directory):
    print(f'COMMANDS: list_directory_in_app - directory={directory}')
    try:
        # Returns a list of all files and directories in the specified directory
        return os.listdir(directory)
    except FileNotFoundError:
        return f"The directory '{directory}' does not exist"
    except NotADirectoryError:
        return f"'{directory}' is not a directory"


def read_file_in_app(file_path, start_line=0, num_lines=100):
    print(
        f'COMMANDS: read_file_in_app - file_path={file_path}, start_line={start_line}, num_lines={num_lines}')
    try:
        lines = []
        total_lines = 0

        # First, count all lines in the file
        with open(file_path, "r") as f:
            for i, line in enumerate(f):
                total_lines += 1

        # Then, read the specific lines
        with open(file_path, "r") as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue
                if len(lines) < num_lines:
                    # Add line number to line content
                    lines.append(f"{i+1}: {line}")
                else:
                    break

        # -1 because line numbers are zero-indexed
        end_line = start_line + len(lines) - 1

        return {
            'content': ''.join(lines),
            'total_lines': total_lines,
            'start_line': start_line,
            'end_line': end_line,
        }
    except FileNotFoundError:
        return f"The file '{file_path}' does not exist"
    except IsADirectoryError:
        return f"'{file_path}' is a directory, not a file"

# Command line
# Example: run_command('dir /path/to/directory')


def run_command(command):
    print(f'COMMANDS: run_command - command_args={command}')
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        return {
            'output': [html.escape(line) for line in result.stdout.splitlines()],
            'error': [html.escape(line) for line in result.stderr.splitlines()],
            'returncode': result.returncode
        }
    except Exception as e:
        return {
            'error': str(e)
        }


def append_error(user_message=None, ai_response=None, error_description=None, error_category=None, resolution_status=None, resolution_description=None, lessons_learned=None):
    df = pd.read_csv(f'{folder_path}/data/errors_data.csv')

    # Set error_id to the next line number in the CSV file
    error_id = len(df) + 1

    # Set date_time to the current time when the function is called
    date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    error_data = {
        "Error ID": error_id,
        "Date & Time": date_time,
        "User Message": user_message,
        "AI Response": ai_response,
        "Error Description": error_description,
        "Error Category": error_category,
        "Resolution Status": resolution_status,
        "Resolution Description": resolution_description,
        "Lessons Learned": lessons_learned
    }
    # Remove None values from the dictionary
    error_data = {k: v for k, v in error_data.items() if v is not None}

    new_error = pd.DataFrame(
        error_data, index=[df.index[-1] + 1 if df.shape[0] > 0 else 0])
    df = pd.concat([df, new_error])
    df.to_csv(f'{folder_path}/data/errors_data.csv', index=False)
    return f"Line was successfully added. Appended line number: {df.index[-1]}"


def update_error(line_number, resolution_status=None, resolution_description=None, lessons_learned=None):
    update_data = {
        "Resolution Status": resolution_status,
        "Resolution Description": resolution_description,
        "Lessons Learned": lessons_learned
    }
    # Remove None values from the dictionary
    update_data = {k: v for k, v in update_data.items() if v is not None}

    df = pd.read_csv(f'{folder_path}/data/errors_data.csv')
    for column, value in update_data.items():
        df.at[line_number, column] = value
    df.to_csv(f'{folder_path}/data/errors_data.csv', index=False)

    return f"Line was successfully updated. Appended line number: {line_number}"
