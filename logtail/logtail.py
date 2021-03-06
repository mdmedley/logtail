from time import sleep
from fnmatch import fnmatch
import os
import sys

file_tracker = {}


def register_existing_files(search_path, name_match):
    for file_, size in get_changed(search_path, name_match, False):
        file_tracker[file_] = size


def get_changed(search_path, name_match, print_new=True):
    current = {}
    for path, dirs, files in os.walk(search_path):
        for f in files:
            if name_match is None or fnmatch(f, name_match):
                file_ = os.path.join(path, f)
                current[file_] = get_file_size(file_)

    for file_ in set(file_tracker) - set(current):
        sys.stdout.write("File removed: {0}\n".format(file_))
        file_tracker.pop(file_)

    for file_, size in current.items():
        if file_ not in file_tracker:
            if print_new:
                sys.stdout.write("New File: {0}\n".format(file_))
            file_tracker[file_] = 0

        if size != file_tracker[file_]:
            yield file_, size


def get_newest_file(search_path, name_match):
    current_time = 0
    current_file = None
    for path, dirs, files in os.walk(search_path):
        for f in files:
            if name_match is not None and not fnmatch(f, name_match):
                continue
            file_path = os.path.join(path, f)
            mtime = os.stat(file_path).st_mtime
            if mtime > current_time:
                current_time = mtime
                current_file = file_path
    return current_file


def get_file_size(path):
    return os.stat(path).st_size


def print_latest(current_file, size):
    if current_file in file_tracker:
        old_size = file_tracker[current_file]
        if size < old_size:
            sys.stdout.write("File Truncated: {0}\n".format(current_file))
            old_size = 0
            file_tracker[current_file] = 0
        if old_size != size:
            with open(current_file, "rb") as f:
                f.seek(old_size)
                sys.stdout.write(f.read(size - old_size))
            file_tracker[current_file] = size
    else:
        with open(current_file, "rb") as f:
            sys.stdout.write(f.read(size))
            file_tracker[current_file] = size


def check_args():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        sys.stdout.write("Usage: taillogs <path> [<file glob>]\n")
        exit(1)

    if not os.path.exists(sys.argv[1]):
        e = IOError("No such file or directory: '{0}'".format(sys.argv[1]))
        e.errno = 2
        raise e

    if len(sys.argv) == 2:
        return sys.argv[1], "*.log"
    else:
        return sys.argv[1], sys.argv[2] or None


def main():
    path, match = check_args()
    register_existing_files(path, match)
    while True:
        for file_, size in get_changed(path, match):
            print_latest(file_, size)
        sleep(.1)


def editlatest():
    path, match = check_args()
    for editor in ["xdg-open", "subl", "vim", "vi", "nano", "pico"]:
        ret_code = os.system("{0} {1}".format(
            os.getenv('EDITOR', editor), get_newest_file(path, match)))
        if not ret_code:
            return ret_code

if __name__ == "__main__":
    main()
