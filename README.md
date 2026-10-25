# MiniOS alpha

## Group Members

Add the names of all group members below:

- Nathaniel Puerto
- Nico Jomento
- Weser Ivan Garcia
- Leo Vince Quezon
- Christian Jolian Borres
- Rc Gallos

## Project Description

MiniOS alpha is a Python-based command-line operating system simulator. It provides a terminal-style interface where users can log in and try basic operating-system concepts, including file and directory management, simulated memory allocation, and simulated process management. It also provides basic utilities such as displaying the current user, date, time, and simulated system information.

MiniOS is a learning project, not a full operating system. Its memory and process features are simulated and do not allocate the computer's actual RAM or launch and terminate real applications.

## Features

- **User login:** Supports the built-in `admin` and `student` accounts.
- **Command-line interface:** Accepts commands through an interactive shell.
- **File management:** Create, read, write, append to, rename, copy, move, and delete files.
- **Directory management:** Create folders, navigate directories, list directory contents, and display a directory tree.
- **Disk-backed virtual file system:** Loads and saves its virtual file tree in a real folder named `MiniOS_Disk` next to the Python script by default.
- **Process simulation:** List simulated processes, start a named simulated process, and terminate a process by PID. Core simulated processes are protected.
- **Memory simulation:** View simulated memory usage, allocate memory in MB, and release allocated memory.
- **System utilities:** Display the date, time, current username, and simulated system information; clear the terminal and exit the program.
- **Error handling:** Displays errors for invalid commands, missing arguments, invalid file operations, and invalid memory or process requests.

## Requirements

- Python 3.x
- A terminal or command-line shell, such as Windows Command Prompt (CMD), PowerShell, or a macOS/Linux terminal
- No third-party Python packages are required by the code shown; it uses Python standard-library modules

## How to Run

1. Make sure Python 3 is installed. You can check with:

   ```bash
   python --version
   ```

2. Clone or download this repository.

3. Open your terminal and navigate to the project folder.

4. Save the MiniOS Python code as `main.py` if it is not already named that way.

5. Run the program:

   ```bash
   python main.py
   ```

   On some systems, you may need to use `python3 main.py` instead.

6. Log in using one of the built-in accounts:

   | Username | Password |
   |---|---|
   | `admin` | `admin123` |
   | `student` | `student123` |

7. At the `MiniOS:/ >`-style prompt, enter a command. Type `help` to display the main command list and file-management help.

## Available Commands

### General and system commands

| Command | Description | Example |
|---|---|---|
| `help` | Displays available commands and file-management commands. | `help` |
| `clear` | Clears the terminal screen. | `clear` |
| `date` | Displays the current date. | `date` |
| `time` | Displays the current time. | `time` |
| `whoami` | Displays the logged-in username. | `whoami` |
| `systeminfo` | Displays simulated OS, version, architecture, CPU, memory, and user information. | `systeminfo` |
| `exit` | Exits MiniOS. | `exit` |

### File and directory commands

| Command | Description | Example |
|---|---|---|
| `dir [path]` | Lists files and folders at the specified path, or in the current directory. | `dir` |
| `ls [path]` | Alias for `dir`. | `ls /` |
| `mkdir <name>` | Creates a directory. Multiple directory paths can be supplied. | `mkdir school` |
| `create <name> [text]` | Creates a file, optionally with starting text. | `create notes.txt "Hello world"` |
| `read <file>` | Displays a file's contents. | `read notes.txt` |
| `type <file>` | Alias for `read`. | `type notes.txt` |
| `cat <file>` | Alias for `read`. | `cat notes.txt` |
| `write <file> <text>` | Replaces a file's contents with the specified text. | `write notes.txt "Updated text"` |
| `append <file> <text>` | Adds text to the end of a file. | `append notes.txt "More text"` |
| `delete <path> [/s]` | Deletes a file or an empty directory. Use `/s` to delete a directory and its contents. | `delete old.txt` or `delete school /s` |
| `del <path> [/s]` | Alias for `delete`. | `del old.txt` |
| `rename <path> <newname>` | Renames a file or directory. | `rename notes.txt notes2.txt` |
| `cd [path]` | Changes the current directory. With no path, returns to the root directory. | `cd school` or `cd ..` |
| `pwd` | Displays the current directory path. | `pwd` |
| `copy <src> <dest>` | Copies a file or directory to a destination. | `copy notes.txt backup.txt` |
| `move <src> <dest>` | Moves a file or directory to a destination. | `move notes.txt school` |
| `tree [path]` | Displays the directory structure for the selected path. | `tree` |
| `fhelp` | Displays file-management command help. | `fhelp` |

### Process management commands

| Command | Description | Example |
|---|---|---|
| `process` | Lists the simulated process table, including process IDs (PIDs), names, and statuses. | `process` |
| `run <name>` | Starts a simulated process with the given name. | `run calculator` |
| `kill <PID>` | Removes a simulated process by PID. The core `system_idle` and `shell` processes cannot be terminated. | `kill 3` |

### Memory management commands

| Command | Description | Example |
|---|---|---|
| `memory` | Displays total, used, and free simulated memory. | `memory` |
| `allocate <MB>` | Allocates a positive whole number of MB in the simulation, if enough simulated memory is available. | `allocate 100` |
| `free <MB>` | Releases a positive whole number of previously allocated MB. Reserved system memory cannot be freed. | `free 100` |

## Notes and Limitations

- The default memory pool is **1,024 MB**, of which **256 MB** is reserved for the simulated system. Initially, **768 MB** is available for user allocations.
- Processes created with `run` are entries in a simulated process table; they do not run real programs.
- File operations are backed by the `MiniOS_Disk` folder. By default, this folder is created next to the Python script and is loaded when MiniOS starts.
- MiniOS synchronizes changes made through its file commands to `MiniOS_Disk`. Keep important files backed up and do not use that folder for unrelated files you cannot afford to lose.
- The built-in usernames and passwords are hard-coded for demonstration. They are not suitable for securing a real system.
