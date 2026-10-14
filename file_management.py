"""
MiniOS - Feature 3: File Management
-----------------------------------
A virtual file system that is mirrored into a REAL folder (MiniOS_Disk) next to
this script, so files and directories really appear in File Explorer.
The program never touches anything outside that folder.

Required commands : dir, mkdir, create, read, delete
Extra commands    : write, append, rename, cd, pwd, copy, move, tree, help

HOW THE CLI TEAMMATE USES THIS MODULE
    from file_management import FileManager, FSError
    fm = FileManager()
    fm.current_user = "admin"            # set after login (User Management)
    output = fm.execute("mkdir", ["Documents"])   # returns a string to print
    # unknown command -> raises FSError("Unknown command") ; use fm.COMMANDS to check

RUN STANDALONE (to test your part):  python file_management.py
"""

import os
import shlex
import shutil
from datetime import datetime


# --------------------------------------------------------------------------
# Errors (the shell just prints str(error))
# --------------------------------------------------------------------------
class FSError(Exception):
    """Base class for every file-management error."""


class NotFound(FSError):
    pass


class AlreadyExists(FSError):
    pass


class NotADirectory(FSError):
    pass


class IsADirectory(FSError):
    pass


class DirNotEmpty(FSError):
    pass


class InvalidName(FSError):
    pass


class InvalidOperation(FSError):
    pass


# --------------------------------------------------------------------------
# Nodes: every file/folder is a Node (similar to an inode)
# --------------------------------------------------------------------------
def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


class Node:
    def __init__(self, name, owner, parent=None):
        self.name = name
        self.owner = owner
        self.parent = parent
        self.created = _now()
        self.modified = self.created


class File(Node):
    def __init__(self, name, owner, parent=None, content=""):
        super().__init__(name, owner, parent)
        self.content = content

    @property
    def size(self):
        return len(self.content)


class Directory(Node):
    def __init__(self, name, owner, parent=None):
        super().__init__(name, owner, parent)
        self.children = {}  # name -> Node

    @property
    def size(self):
        return 0


# --------------------------------------------------------------------------
# File system core (never prints; returns data or raises FSError)
# --------------------------------------------------------------------------
INVALID_CHARS = '<>:"/\\|?*'


class FileSystem:
    def __init__(self, owner="admin"):
        self.root = Directory("", owner)
        self.cwd = self.root
        self.current_user = owner

    # ---- path helpers ----
    @staticmethod
    def _norm(path):
        return path.replace("\\", "/")

    def path_of(self, node):
        parts = []
        while node.parent is not None:
            parts.append(node.name)
            node = node.parent
        return "/" + "/".join(reversed(parts))

    def resolve(self, path):
        """Turn a path string into a node. Supports absolute, relative, . and .."""
        path = self._norm(path)
        node = self.root if path.startswith("/") else self.cwd
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                node = node.parent or node
                continue
            if not isinstance(node, Directory):
                raise NotADirectory(f"'{node.name}' is not a directory.")
            if part not in node.children:
                raise NotFound(f"'{path}' was not found.")
            node = node.children[part]
        return node

    def _split(self, path):
        """Return (parent_directory, final_name) for a path that may not exist yet."""
        path = self._norm(path).rstrip("/")
        if not path:
            raise InvalidName("Path cannot be empty.")
        parent_path, _, name = path.rpartition("/")
        if parent_path == "":
            parent = self.root if path.startswith("/") else self.cwd
        else:
            parent = self.resolve(parent_path)
        if not isinstance(parent, Directory):
            raise NotADirectory(f"'{parent_path}' is not a directory.")
        self._check_name(name)
        return parent, name

    @staticmethod
    def _check_name(name):
        if not name or name in (".", ".."):
            raise InvalidName(f"'{name}' is not a valid name.")
        if any(c in INVALID_CHARS for c in name):
            raise InvalidName(f"Name cannot contain any of: {INVALID_CHARS}")
        if len(name) > 255:
            raise InvalidName("Name is too long (max 255 characters).")

    def _is_inside(self, node, ancestor):
        """True if node is ancestor itself or lives anywhere below it."""
        while node is not None:
            if node is ancestor:
                return True
            node = node.parent
        return False

    # ---- operations ----
    def listdir(self, path="."):
        node = self.resolve(path)
        if isinstance(node, File):
            return node, [node]
        return node, sorted(node.children.values(),
                            key=lambda n: (isinstance(n, File), n.name.lower()))

    def mkdir(self, path):
        parent, name = self._split(path)
        if name in parent.children:
            raise AlreadyExists(f"'{name}' already exists.")
        parent.children[name] = Directory(name, self.current_user, parent)
        parent.modified = _now()

    def create(self, path, content=""):
        parent, name = self._split(path)
        if name in parent.children:
            raise AlreadyExists(f"'{name}' already exists.")
        parent.children[name] = File(name, self.current_user, parent, content)
        parent.modified = _now()

    def read(self, path):
        node = self.resolve(path)
        if isinstance(node, Directory):
            raise IsADirectory(f"'{node.name or '/'}' is a directory, not a file.")
        return node.content

    def write(self, path, text, append=False):
        node = self.resolve(path)
        if isinstance(node, Directory):
            raise IsADirectory(f"'{node.name or '/'}' is a directory, not a file.")
        node.content = node.content + text if append else text
        node.modified = _now()

    def delete(self, path, recursive=False):
        node = self.resolve(path)
        if node is self.root:
            raise InvalidOperation("Cannot delete the root directory.")
        if self._is_inside(self.cwd, node):
            raise InvalidOperation("Cannot delete the current directory "
                                   "(or one that contains it). Use cd first.")
        if isinstance(node, Directory) and node.children and not recursive:
            raise DirNotEmpty(f"Directory '{node.name}' is not empty. "
                              "Use 'delete <dir> /s' to delete it and its contents.")
        del node.parent.children[node.name]
        node.parent.modified = _now()
        return isinstance(node, Directory)

    def rename(self, path, new_name):
        node = self.resolve(path)
        if node is self.root:
            raise InvalidOperation("Cannot rename the root directory.")
        self._check_name(new_name)
        if new_name in node.parent.children:
            raise AlreadyExists(f"'{new_name}' already exists.")
        del node.parent.children[node.name]
        node.name = new_name
        node.parent.children[new_name] = node
        node.modified = _now()

    def cd(self, path):
        node = self.resolve(path)
        if not isinstance(node, Directory):
            raise NotADirectory(f"'{node.name}' is not a directory.")
        self.cwd = node

    def _clone(self, node, new_parent, new_name):
        if isinstance(node, File):
            copy = File(new_name, self.current_user, new_parent, node.content)
        else:
            copy = Directory(new_name, self.current_user, new_parent)
            for child in node.children.values():
                copy.children[child.name] = self._clone(child, copy, child.name)
        return copy

    def _dest(self, src, dest_path):
        """Work out destination parent + name. If dest is a directory, keep src name."""
        try:
            d = self.resolve(dest_path)
            if isinstance(d, Directory):
                return d, src.name
            raise AlreadyExists(f"'{d.name}' already exists.")
        except NotFound:
            return self._split(dest_path)

    def copy(self, src_path, dest_path):
        src = self.resolve(src_path)
        if src is self.root:
            raise InvalidOperation("Cannot copy the root directory.")
        parent, name = self._dest(src, dest_path)
        if self._is_inside(parent, src):
            raise InvalidOperation("Cannot copy a directory into itself.")
        if name in parent.children:
            raise AlreadyExists(f"'{name}' already exists in the destination.")
        parent.children[name] = self._clone(src, parent, name)
        parent.modified = _now()

    def move(self, src_path, dest_path):
        src = self.resolve(src_path)
        if src is self.root:
            raise InvalidOperation("Cannot move the root directory.")
        parent, name = self._dest(src, dest_path)
        if self._is_inside(parent, src):
            raise InvalidOperation("Cannot move a directory into itself.")
        if name in parent.children:
            raise AlreadyExists(f"'{name}' already exists in the destination.")
        del src.parent.children[src.name]
        src.name, src.parent = name, parent
        parent.children[name] = src
        parent.modified = _now()

    def tree(self, path="."):
        start = self.resolve(path)
        if not isinstance(start, Directory):
            raise NotADirectory(f"'{start.name}' is not a directory.")
        lines = [self.path_of(start)]

        def walk(directory, prefix):
            items = sorted(directory.children.values(),
                           key=lambda n: (isinstance(n, File), n.name.lower()))
            for i, child in enumerate(items):
                last = i == len(items) - 1
                lines.append(prefix + ("`-- " if last else "|-- ") + child.name)
                if isinstance(child, Directory):
                    walk(child, prefix + ("    " if last else "|   "))

        walk(start, "")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# Real-disk backing: mirrors the virtual tree into ONE real folder
# --------------------------------------------------------------------------
class DiskBacking:
    """Keeps a real folder (default: MiniOS_Disk next to this script) in sync
    with the virtual file system. It never touches anything outside that folder."""

    def __init__(self, folder):
        self.root = os.path.abspath(folder)
        os.makedirs(self.root, exist_ok=True)

    def _safe(self, path):
        path = os.path.abspath(path)
        if os.path.commonpath([path, self.root]) != self.root:
            raise FSError("Refusing to touch a path outside the MiniOS_Disk folder.")
        return path

    def load(self, fs):
        """Rebuild the virtual tree from what is already in the real folder."""
        def walk(real, node):
            for entry in sorted(os.listdir(real)):
                path = os.path.join(real, entry)
                if os.path.isdir(path):
                    child = Directory(entry, fs.current_user, node)
                    node.children[entry] = child
                    walk(path, child)
                else:
                    with open(path, "r", encoding="utf-8", errors="replace",
                              newline="") as f:
                        node.children[entry] = File(entry, fs.current_user, node,
                                                    f.read())
        walk(self.root, fs.root)

    def save(self, fs):
        """Make the real folder match the virtual tree exactly."""
        def sync(node, real):
            real = self._safe(real)
            os.makedirs(real, exist_ok=True)
            for entry in os.listdir(real):          # remove what no longer exists
                if entry not in node.children:
                    path = self._safe(os.path.join(real, entry))
                    shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
            for name, child in node.children.items():
                path = self._safe(os.path.join(real, name))
                if isinstance(child, Directory):
                    if os.path.isfile(path):
                        os.remove(path)
                    sync(child, path)
                else:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    with open(path, "w", encoding="utf-8", newline="") as f:
                        f.write(child.content)
        sync(fs.root, self.root)


# --------------------------------------------------------------------------
# Command layer: turns "command + args" into a printable string
# --------------------------------------------------------------------------
HELP_TEXT = """File commands:
  dir [path]               List files and folders
  mkdir <name>             Create a directory
  create <name> [text]     Create a file (optional starting text)
  read <file>              Show a file's contents
  delete <path> [/s]       Delete a file or directory (/s = non-empty directory)
  write <file> <text>      Overwrite a file's contents
  append <file> <text>     Add text to the end of a file
  rename <path> <newname>  Rename a file or directory
  cd [path]                Change directory (cd .. goes up, cd / goes to root)
  pwd                      Show current directory
  copy <src> <dest>        Copy a file or directory
  move <src> <dest>        Move a file or directory
  tree [path]              Show directory structure"""


class FileManager:
    COMMANDS = ("dir", "ls", "mkdir", "create", "read", "type", "cat", "delete",
                "del", "write", "append", "rename", "cd", "pwd", "copy", "move",
                "tree", "fhelp")

    MUTATING = ("mkdir", "create", "delete", "write", "append", "rename",
                "copy", "move")

    def __init__(self, owner="admin", folder=None):
        self.fs = FileSystem(owner)
        if folder is None:
            folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "MiniOS_Disk")
        self.disk = DiskBacking(folder)
        self.disk.load(self.fs)

    # The user-management teammate sets this after login.
    @property
    def current_user(self):
        return self.fs.current_user

    @current_user.setter
    def current_user(self, name):
        self.fs.current_user = name

    def prompt(self):
        return f"MiniOS:{self.fs.path_of(self.fs.cwd)}> "

    def execute(self, command, args):
        """Run one file command. Returns text to print, or raises FSError."""
        command = command.lower()
        command = {"ls": "dir", "type": "read", "cat": "read",
                   "del": "delete"}.get(command, command)
        handler = getattr(self, "_cmd_" + command, None)
        if handler is None:
            raise FSError(f"'{command}' is not a file command.")
        result = handler(args)
        if command in self.MUTATING:
            self.disk.save(self.fs)      # write the change to the real folder
        return result

    @staticmethod
    def _need(args, minimum, usage):
        if len(args) < minimum:
            raise FSError(f"Missing argument. Usage: {usage}")

    # ---- handlers ----
    def _cmd_dir(self, args):
        node, items = self.fs.listdir(args[0] if args else ".")
        shown = self.fs.path_of(node if isinstance(node, Directory) else node.parent)
        lines = [f" Directory of {shown}", ""]
        files = folders = total = 0
        for n in items:
            if isinstance(n, Directory):
                folders += 1
                lines.append(f"{n.modified}    {'<DIR>':>9}  {n.name}")
            else:
                files += 1
                total += n.size
                lines.append(f"{n.modified}    {n.size:>9}  {n.name}")
        lines.append("")
        lines.append(f"{files:>8} File(s)  {total} bytes")
        lines.append(f"{folders:>8} Dir(s)")
        return "\n".join(lines)

    def _cmd_mkdir(self, args):
        self._need(args, 1, "mkdir <name>")
        for name in args:
            self.fs.mkdir(name)
        return "Directory created."

    def _cmd_create(self, args):
        self._need(args, 1, "create <name> [text]")
        self.fs.create(args[0], " ".join(args[1:]))
        return "File created."

    def _cmd_read(self, args):
        self._need(args, 1, "read <file>")
        content = self.fs.read(args[0])
        return content if content else "(file is empty)"

    def _cmd_delete(self, args):
        self._need(args, 1, "delete <path> [/s]")
        recursive = any(a.lower() == "/s" for a in args)
        targets = [a for a in args if a.lower() != "/s"]
        self._need(targets, 1, "delete <path> [/s]")
        was_dir = self.fs.delete(targets[0], recursive)
        return "Directory deleted." if was_dir else "File deleted."

    def _cmd_write(self, args):
        self._need(args, 2, "write <file> <text>")
        self.fs.write(args[0], " ".join(args[1:]))
        return "File written."

    def _cmd_append(self, args):
        self._need(args, 2, "append <file> <text>")
        self.fs.write(args[0], " ".join(args[1:]), append=True)
        return "Text appended."

    def _cmd_rename(self, args):
        self._need(args, 2, "rename <path> <newname>")
        self.fs.rename(args[0], args[1])
        return "Renamed."

    def _cmd_cd(self, args):
        self.fs.cd(args[0] if args else "/")
        return ""

    def _cmd_pwd(self, args):
        return self.fs.path_of(self.fs.cwd)

    def _cmd_copy(self, args):
        self._need(args, 2, "copy <src> <dest>")
        self.fs.copy(args[0], args[1])
        return "Copied."

    def _cmd_move(self, args):
        self._need(args, 2, "move <src> <dest>")
        self.fs.move(args[0], args[1])
        return "Moved."

    def _cmd_tree(self, args):
        return self.fs.tree(args[0] if args else ".")

    def _cmd_fhelp(self, args):
        return HELP_TEXT


# --------------------------------------------------------------------------
# Standalone test shell (your CLI teammate will replace this with the real one)
# --------------------------------------------------------------------------
def run_standalone():
    fm = FileManager()
    print("MiniOS File Management test shell. Type 'fhelp' for commands, 'exit' to quit.")
    print(f"Real files are stored in: {fm.disk.root}")
    while True:
        try:
            line = input(fm.prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break
        try:
            # backslashes -> slashes first so Windows paths survive shlex
            parts = shlex.split(line.replace("\\", "/"))
        except ValueError:
            print("Error: unbalanced quotes.")
            continue
        try:
            out = fm.execute(parts[0], parts[1:])
            if out:
                print(out)
        except FSError as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    run_standalone()
