import subprocess
import os

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
                lines.append(line)
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
                    lines.append(line)
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
