import os
import json
from cryptography.fernet import Fernet
import threading
import subprocess
import tempfile

class FileSystem:
    def __init__(self, rootdir="~"):
        self.rootdir = rootdir
        self.file_structure = {}
        self.current_path = self.rootdir
        self.load_filesystem()

    def load_filesystem(self):
        # load filesystem structure from a JSON file if it exists
        if os.path.exists("filesystem.json"):
            with open("filesystem.json", "r") as file:
                self.file_structure = json.load(file)
        else:
            # initialize with a basic structure if no file exists
            self.file_structure = {
                "~": {
                    "users": {}
                }
            }
            self.save_filesystem()

    def save_filesystem(self):
        # save the filesystem structure to a JSON file
        # use backslashes for all paths in the filesystem
        def convert_paths(obj):
            if isinstance(obj, dict):
                return {key.replace("/", "\\"): convert_paths(value) for key, value in obj.items()}
            return obj

        with open("filesystem.json", "w") as file:
            json.dump(convert_paths(self.file_structure), file, indent=4)

    def resolve_path(self, path):
        # resolve absolute and relative paths using backslashes
        if path == "~":
            return self.rootdir  # ~ is the root
        if path.startswith("~/"):
            return os.path.join(self.rootdir, path[2:]).replace("/", "\\")
        if path.startswith("\\"):
            return os.path.join(self.rootdir, path[1:]).replace("/", "\\")
        return os.path.join(self.current_path, path).replace("/", "\\")

    def change_directory(self, path):
        # change the current directory
        new_path = self.resolve_path(path)
        dirs = new_path.split("\\")  # split by backslash
        node = self.file_structure

        try:
            for directory in dirs:
                if directory and directory in node:
                    node = node[directory]
                elif directory:
                    raise FileNotFoundError

            self.current_path = new_path
            return f"Current directory: {self.current_path}"
        except FileNotFoundError:
            return f"Path '{path}' does not exist."

    def list_contents(self):
        # list contents of the current directory
        dirs = self.current_path.split("\\")  # split by backslash
        node = self.file_structure
        for directory in dirs:
            if directory:
                node = node.get(directory, {})
        return list(node.keys())

    def make_directory(self, directory_name):
        # create a new directory
        dirs = self.current_path.split("\\")  # split by backslash
        node = self.file_structure
        for directory in dirs:
            if directory:
                node = node.setdefault(directory, {})
        if directory_name in node:
            return f"Directory '{directory_name}' already exists."
        node[directory_name] = {}
        self.save_filesystem()
        return f"Directory '{directory_name}' created."

    def read_file(self, file_path):
        # read a file and return its content
        full_path = self.resolve_path(file_path)  # resolve path relative to current directory
        path_parts = full_path.split("\\")  # split the path by backslash for traversal
        
        # traverse json structure
        node = self.file_structure
        for part in path_parts[:-1]:
            if part in node:
                node = node[part]
            else:
                raise FileNotFoundError(f"Directory '{part}' not found in path '{file_path}'.")

        # check if the file exists and is a string (file content)
        file_name = path_parts[-1]
        if file_name in node and isinstance(node[file_name], str):
            return node[file_name]
        elif file_name not in node:
            raise FileNotFoundError(f"File '{file_name}' not found in path '{file_path}'.")
        else:
            raise ValueError(f"Path '{file_path}' is not a file.")

    def edit_file(self, file_path, content):
        # edit or create a file
        full_path = file_path.split("\\")  # split by backslash
        node = self.file_structure
        for part in full_path[:-1]:
            if part:
                node = node.setdefault(part, {})
        node[full_path[-1]] = content
        self.save_filesystem()
        return f"File '{file_path}' updated successfully."
    
    def nano(self, file_path):
        #edit a file using a simple text editor
        # make sure that the file path is resolved relative to the current directory
        full_path = self.resolve_path(file_path)
        
        # check if file exists
        if full_path not in self.file_structure:
            print(f"File '{file_path}' does not exist. Creating new file.")
            content = ""
        else:
            # read the current file content if it exists
            content = self.read_file(full_path)

        print(f"Editing file: {file_path}\n")
        print("Type your content below. Type 'SAVE' to save and exit.")

        while True:
            line = input()
            if line.strip().upper() == "SAVE":
                # save the content to the file
                self.edit_file(full_path, content)
                print(f"File '{file_path}' saved.")
                break
            else:
                # add the line to the content
                content += line + "\n"

    def create_user_directory(self, username):
        # create a home directory structure for a new user
        # make sure the 'users' directory exists
        users_node = self.file_structure.setdefault("~", {}).setdefault("users", {})

        # create the specific users directory structure
        if username not in users_node:
            users_node[username] = {
                "Home": {
                    "Documents": {},  # empty directory for documents
                    "Downloads": {},  # empty directory for downloads
                }
            }
            self.save_filesystem()
            print(f"Home directory for user '{username}' created.")
        else:
            print(f"User '{username}' already has a home directory.")

    def set_user_home(self, username):
        # set the current path to the user's home directory
        user_home_path = os.path.join("~", "users", username, "Home").replace("/", "\\")
        print(f"Resolving home directory for user '{username}': {user_home_path}")

        dirs = user_home_path.split("\\")
        node = self.file_structure

        for directory in dirs:
            if directory and directory in node:
                node = node[directory]
            elif directory:
                raise FileNotFoundError(f"Home directory for user '{username}' does not exist.")

        self.current_path = user_home_path
        return f"Current directory set to {self.current_path}."


class UserSystem:
    def __init__(self):
        self.users = {}
        self.logged_in_user = None
        self.key = self.load_or_generate_key()
        self.cipher = Fernet(self.key)
        self.load_users()

    def load_or_generate_key(self):
        # load the encryption key from disk, or generate a new one
        if os.path.exists('secret.key'):
            with open('secret.key', 'rb') as file:
                return file.read()
        else:
            key = Fernet.generate_key()
            with open('secret.key', 'wb') as file:
                file.write(key)
            return key

    def load_users(self):
        # load users from the encrypted file
        if os.path.exists('users.json'):
            with open('users.json', 'r') as file:
                encrypted_data = json.load(file)
                for username, user_data in encrypted_data.items():
                    # decrypt stored password
                    decrypted_password = self.cipher.decrypt(user_data["password"].encode()).decode()
                    self.users[username] = {"password": decrypted_password, "admin": user_data["admin"]}

    def save_users(self):
        # save the users' encrypted passwords to disk
        encrypted_data = {}
        for username, user_data in self.users.items():
            # encrypt password before saving
            encrypted_password = self.cipher.encrypt(user_data["password"].encode()).decode()
            encrypted_data[username] = {"password": encrypted_password, "admin": user_data["admin"]}

        with open('users.json', 'w') as file:
            json.dump(encrypted_data, file, indent=4)

    def create_user(self, username, password, admin_mode=False):
        if username in self.users:
            return f"User '{username}' already exists."

        encrypted_password = self.cipher.encrypt(password.encode()).decode()
        self.users[username] = {"password": encrypted_password, "admin": admin_mode}
        self.save_users()
        return f"User '{username}' created."

    def validate_password(self, username, password):
        # validate the user's password by comparing the decrypted version
        if username in self.users:
            # decrypt stored encrypted password
            decrypted_password = self.cipher.decrypt(self.users[username]["password"].encode()).decode()
            return decrypted_password == password
        return False

    def login(self, username, password):
        # log in a user by validating their password
        if self.validate_password(username, password):
            self.logged_in_user = username
            return f"Logged in as {username}."
        return "Invalid username or password."

    def logout(self):
        # log out the current user."""
        if self.logged_in_user:
            self.logged_in_user = None
            return "Logged out successfully."
        return "No user is currently logged in."
    
class SubprocessManager:
    def __init__(self):
        self.processes = {}  # Mapping of filename -> process object
        self.lock = threading.Lock()
        self.fs = FileSystem()
        
    def get_file_content(self, virtual_path, filesystem):
        parts = virtual_path.strip('~').split('/')
        current = filesystem['~']
        for part in parts:
            if part in current:
                current = current[part]
            else:
                raise FileNotFoundError(f"File '{virtual_path}' not found in virtual filesystem.")
        if isinstance(current, str):
            return current
        else:
            raise FileNotFoundError(f"File '{virtual_path}' not found in virtual filesystem.")

    def start_process(self, virtual_path):
        with self.lock:
            try:
                # Load the virtual filesystem
                filesystem = self.fs.load_filesystem()

                # Get the content of the Python file from the virtual filesystem
                content = self.get_file_content(virtual_path, filesystem)

                # Replace \n with actual newline characters
                formatted_content = content.replace('\\n', '\n')

                # Write the formatted content to a temporary Python file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
                    temp_file.write(formatted_content.encode('utf-8'))
                    temp_file_path = temp_file.name

                # Run the temporary Python script in the background
                process = subprocess.Popen(
                    ["python", temp_file_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.processes[temp_file_path] = process
                return f"Started process for '{temp_file_path}'."
            except Exception as e:
                return f"Failed to start process: {str(e)}"

    def read_output(self, file_path):
        with self.lock:
            if file_path not in self.processes:
                return f"No running process found for '{file_path}'."

            process = self.processes[file_path]
            try:
                output, errors = process.communicate(timeout=1)  # Non-blocking read
                return f"Output:\n{output}\nErrors:\n{errors}"
            except subprocess.TimeoutExpired:
                return "The process is still running."

    def list_processes(self):
        # List all running processes
        with self.lock:
            if not self.processes:
                return "No processes are currently running."
            return "\n".join([f"{i+1}. {file}" for i, file in enumerate(self.processes.keys())])

    def focus_process(self, file_path):
        # Focus on a specific process to see its output
        with self.lock:
            if file_path not in self.processes:
                return f"No running process found for '{file_path}'."

            process = self.processes[file_path]
            if process.poll() is not None:  # Check if process has exited
                self.processes.pop(file_path)
                return f"Process '{file_path}' has already terminated."

            # Read the output and error streams
            try:
                output, errors = process.communicate(timeout=1)  # Non-blocking read
                return f"Output:\n{output}\nErrors:\n{errors}"
            except subprocess.TimeoutExpired:
                return "The process is still running."

    def terminate_process(self, file_path):
        # Terminate a specific process
        with self.lock:
            if file_path not in self.processes:
                return f"No running process found for '{file_path}'."

            process = self.processes[file_path]
            process.terminate()
            process.wait()  # Wait for the process to exit
            self.processes.pop(file_path)
            return f"Terminated process for '{file_path}'."

class FileImporter:
    def __init__(self, file_system):
        self.fs = file_system

    def import_file(self, source_path, destination_path):
        if not os.path.isfile(source_path):
            return f"Error: Source file '{source_path}' does not exist."

        # Read the file's content
        try:
            with open(source_path, 'r') as file:
                content = file.read()
        except Exception as e:
            return f"Error reading file '{source_path}': {e}"

        # Add the file to the simulated filesystem
        try:
            self.fs.edit_file(destination_path, content)
            return f"File '{source_path}' successfully imported to '{destination_path}'."
        except Exception as e:
            return f"Error importing file: {e}"

    def list_real_files(self, directory):
        if not os.path.isdir(directory):
            return f"Error: Directory '{directory}' does not exist."

        try:
            return os.listdir(directory)
        except Exception as e:
            return f"Error accessing directory '{directory}': {e}"


class Commands:
    def __init__(self, file_system, user_system):
        self.fs = file_system
        self.user_system = user_system
        self.subprocess_manager = SubprocessManager()
        self.file_importer = FileImporter(file_system)
        self.command_info = {
            "cd": {
                "description": "Change the current directory.",
                "syntax": "cd <path>",
                "example": "cd ~\\users\\admin\\Home\\Documents",
                "function": self.fs.change_directory,
            },
            "ls": {
                "description": "List contents of the current directory.",
                "syntax": "ls",
                "example": "ls",
                "function": lambda: "\n".join(self.fs.list_contents()),
            },
            "mkdir": {
                "description": "Create a new directory.",
                "syntax": "mkdir <directory_name>",
                "example": "mkdir new_folder",
                "function": self.fs.make_directory,
            },
            "create_user": {
                "description": "Create a new user (admin-only).",
                "syntax": "create_user <username> <password> <admin_mode>",
                "example": "create_user alice password123 true",
                "function": self.create_user,
            },
            "login": {
                "description": "Log in as a specific user.",
                "syntax": "login <username> <password>",
                "example": "login admin admin123",
                "function": self.login_user,
            },
            "logout": {
                "description": "Log out of the current user session.",
                "syntax": "logout",
                "example": "logout",
                "function": self.logout_user,
            },
            "help": {
                "description": "Display the help menu.",
                "syntax": "help",
                "example": "help",
                "function": self.help_command,
            },
            "nano": {
                "description": "Edit a file using the nano editor.",
                "syntax": "nano <file_path>",
                "example": "nano ~/users/admin/Home/Documents/note.txt",
                "function": self.nano_file,
            },
            "read_file": {
                "description": "Read the contents of a file.",
                "syntax": "read_file <file_path>",
                "example": "read_file ~/users/admin/Home/Documents/note.txt",
                "function": self.fs.read_file,
            },
            "subprocess_start": {
                "description": "Start a Python file as a background process.",
                "syntax": "subprocess_start <file_path>",
                "example": "subprocess_start example.py",
                "function": self.subprocess_start,
            },
            "subprocess_list": {
                "description": "List all running background processes.",
                "syntax": "subprocess_list",
                "example": "subprocess_list",
                "function": lambda: self.subprocess_manager.list_processes(),
            },
            "subprocess_focus": {
                "description": "Focus on a specific process and display its output.",
                "syntax": "subprocess_focus <file_path>",
                "example": "subprocess_focus example.py",
                "function": self.subprocess_focus,
            },
            "subprocess_terminate": {
                "description": "Terminate a specific background process.",
                "syntax": "subprocess_terminate <file_path>",
                "example": "subprocess_terminate example.py",
                "function": self.subprocess_terminate,
            },
            "subprocess_list":{
                "description": "List all running background processes.",
                "syntax": "subprocess_list",
                "example": "subprocess_list",
                "function": self.subprocess_list,
            },
            "import_file": {
                "description": "Import a Python file from the real filesystem to the virtual filesystem.",
                "syntax": "import_file <source_path> <destination_path>",
                "example": "import_file C:\\path\\to\\file.py ~\\users\\admin\\Home\\Documents\\file.py",
                "function": self.import_file,
            },
            "list_real_files": {
                "description": "List all files in a real directory on the host filesystem.",
                "syntax": "list_real_files <directory>",
                "example": "list_real_files C:\\path\\to\\directory",
                "function": self.list_real_files,
            },
        }

    def create_user(self, username, password, admin_mode):
        if username in self.user_system.users:
            return f"User '{username}' already exists."
        admin_mode = admin_mode.lower() == "true"
        result = self.user_system.create_user(username, password, admin_mode)
        if "created" in result:
            self.fs.create_user_directory(username)
        return result

    def login_user(self, username, password):
        result = self.user_system.login(username, password)
        if "Logged in" in result:
            try:
                # set current directory to users home
                self.fs.set_user_home(username)
            except FileNotFoundError as e:
                return str(e)
        return result

    def logout_user(self):
        return self.user_system.logout()
    
    def nano_file(self, file_path):
        """Invoke nano command to edit a file."""
        self.fs.nano(file_path)

    def subprocess_start(self, file_path):
        # Start a subprocess for a Python file
        resolved_path = self.fs.resolve_path(file_path)
        return self.subprocess_manager.start_process(resolved_path)

    def subprocess_focus(self, file_path):
        # Focus on a subprocess for a Python file
        resolved_path = self.fs.resolve_path(file_path)
        return self.subprocess_manager.focus_process(resolved_path)

    def subprocess_terminate(self, file_path):
        # Terminate a subprocess for a Python file
        resolved_path = self.fs.resolve_path(file_path)
        return self.subprocess_manager.terminate_process(resolved_path)
    
    def subprocess_list(self):
        # List all running processes
        return self.subprocess_manager.list_processes()
    
    def subprocess_read(self, file_path):
        # Read the output of a specific process
        resolved_path = self.fs.resolve_path(file_path)
        return self.subprocess_manager.read_output(resolved_path)
    
    def import_file(self, source_path, destination_path):
        """
        Import a Python file using FileImporter.
        """
        return self.file_importer.import_file(source_path, destination_path)

    def list_real_files(self, directory):
        """
        List real files in a host directory using FileImporter.
        """
        result = self.file_importer.list_real_files(directory)
        if isinstance(result, list):
            return "\n".join(result)
        return result

    def help_command(self):
        """Display available commands."""
        help_text = "Available commands:\n"
        for cmd, info in self.command_info.items():
            help_text += f" - {cmd}: {info['description']}\n"
            help_text += f"   Syntax: {info['syntax']}\n"
            help_text += f"   Example: {info['example']}\n"
        return help_text

    def execute(self, cmd, args):
        if cmd in self.command_info:
            func = self.command_info[cmd]["function"]
            try:
                return func(*args)
            except TypeError:
                return f"Invalid syntax. Correct usage: {self.command_info[cmd]['syntax']}"
            except Exception as e:
                return str(e)
        else:
            return f"Command '{cmd}' not recognized."


class PythonOS:
    def __init__(self):
        self.fs = FileSystem()
        self.user_system = UserSystem()
        self.commands = Commands(self.fs, self.user_system)

        # automatically create the admin user if not already present
        if "admin" not in self.user_system.users:
            result = self.commands.create_user("admin", "admin123", "true")
            print(result)  # show admin creation status
            self.fs.create_user_directory("admin")  # create admins home directory

    def boot(self):
        print("Booting PiPiOS...")
        print("Thinking of adding custom services soon but idk when :p")

    def show_login_screen(self):
        """Displays the login screen until a user successfully logs in."""
        while not self.user_system.logged_in_user:
            print("\nPlease log in.")
            usrname = input("Enter username: ").strip()
            passwd = input("Enter password: ").strip()
            result = self.user_system.login(usrname, passwd)
            print(result)
            if self.user_system.logged_in_user:
                print(f"Welcome, {usrname}!\n")
                try:
                    # set current directory to the users home directory after successful login
                    self.fs.set_user_home(usrname)
                except FileNotFoundError as e:
                    print(f"Error: {str(e)}")
                    continue
            else:
                print("Invalid username or password. Please try again.")

    def main(self):
        while True:
            if self.user_system.logged_in_user:
                cmd_input = input(f"{self.fs.current_path} > ").strip()
                if cmd_input == "exit":
                    print("Shutting down...")
                    break

                parts = cmd_input.split()
                cmd = parts[0]
                args = parts[1:]

                if cmd == "help":
                    print(self.commands.help_command())
                else:
                    print(self.commands.execute(cmd, args))
            else:
                os.system("cls" if os.name == "nt" else "clear")
                self.show_login_screen()


# Start the OS
os_instance = PythonOS()
os_instance.boot()
os_instance.main()
