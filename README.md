# PiPiOS

<div align="center">
  <h3>Views</h3>
  <img src="https://moe-counter.glitch.me/get/@:hidokipipi" align="center" />
  <h4></h4>
</div>


PiPiOS is a simulated operating system built with Python, featuring a simple file system, user management, and a command-line interface. It allows users to create directories, edit files, manage user accounts, and more.

---

## Features

- **File System**:
  - Create directories and files.
  - Edit files using a simple text editor (`nano`).
  - Save the filesystem structure in a JSON file.

- **User Management**:
  - Create users with encrypted passwords.
  - Differentiate between admin and non-admin users.
  - Login and logout functionality with a secure login screen.

- **Command-Line Interface**:
  - Commands like `cd`, `ls`, `mkdir`, `nano`, `login`, `logout`, and more.
  - Dynamic paths with support for relative and absolute navigation.

---

## Commands

| Command|Description|Syntax|Example|
|--------|-----------|-------|------|
|**`cd`**|Change the current directory.| `cd <path>`| `cd ~\users\admin\Home\Documents`|
|**`ls`**|List the contents of the current directory.| `ls`| `ls`|
|**`mkdir`**|Create a new directory.| `mkdir <directory_name>`| `mkdir my_folder`|
|**`nano`**|Edit or create a file using a simple text editor.| `nano <file_path>`| `nano cool.txt`|
|**`read_file`**|Display the contents of a file.| `read_file <file_path>`| `read_file cool.txt`|
|**`create_user`**|Create a new user. (Admins only).| `create_user <username> <password>`| `create_user alice pass123`|
|**`login`**|Log in to an existing user account.| `login <username> <password>`| `login admin admin123`|
|**`logout`**|Log out from the current session.| `logout`| `logout`|
|**`help`**|Display a list of available commands with usage examples.| `help`| `help`|

---

## How It Works

### File System
- The file system is represented as a nested dictionary and is saved/loaded from `filesystem.json`.
- Directories are stored as nested dictionaries, and files are stored as key-value pairs where the value is the file content.

### User Management
- User accounts are stored in `users.json`, with encrypted passwords using the `cryptography` library.
- Only logged-in users can access the file system.
- Admin users have additional permissions (e.g., creating new users).

---

## Getting Started

### Prerequisites
- Python 3.7 or higher
- Install dependencies:
  ```bash
  pip install cryptography
  ```

### Running PiPiOS
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PiPiOS.git
   cd PiPiOS
   ```
2. Run the main script:
   ```bash
   python main.py
   ```

### Example Usage
1. Log in as the default admin (`admin` with password `admin123`).
2. Create a new user:
   ```plaintext
   ~ > create_user alice password123 True
   ```
3. Switch to the new user:
   ```plaintext
   ~ > logout
   ~ > login alice password123
   ```

---

## File Structure
```plaintext
.\
├── main.py         # Main script to run PiPiOS
├── filesystem.json # JSON file representing the file system structure
├── users.json      # JSON file storing user data (encrypted passwords)
├── secret.key      # Encryption key for securing user passwords
```

---

## Future Features
- Add permissions for user-specific directories and files.
- Improve the file editor with more functionality.
- Implement file copy, move, and delete commands.

---

## License
This project is licensed under the MIT License. See `LICENSE` for more details.

---

## Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.
