#!/usr/bin/env python

import shutil as sh
import os
from sys import argv, exit
import getopt as g


def main():
    # Parse options ------------------------------------------------------------
    options = "qhd:m:"
    try:
        opts, args = g.getopt(argv[1:], options)
    except g.GetoptError as err:
        print(str(err))
        usage(os.path.basename(argv[0]))
        return 1

    QUIET = False
    LIN_DIR = os.getcwd()
    MODES = ("push", "pull", "both")
    MODE = "both"   # Default: sync both ways
    for opt, arg in opts:
        if opt == "-q":                     # Option q - Quiet mode, don't print
            QUIET = True
        elif opt == "-h":
            usage(os.path.basename(argv[0]))
            return 0
        elif opt == "-d":                   # Option d - Specify a directory
            LIN_DIR = arg
        elif opt == "-m":                   # Option m - Specify sync mode
            if arg.lower() in MODES:
                MODE = arg.lower()
            else:
                print("Error: invalid mode")
                usage(os.path.basename(argv[0]))
                return 1
    # --------------------------------------------------------------------------
    # Check that Windows partition is actually writeable
    if not writable():
        if (not QUIET) and (MODE != "pull"):
            print("Error: Windows partition mounted as read-only. ", end="")
            if MODE == "both":
                print("Pulling only")
                MODE = "pull"
            else:
                print()
                return 1
    # --------------------------------------------------------------------------

    sync(LIN_DIR, MODE, QUIET)

    return 0


# Print usage message upon error
def usage(fname):
    print("usage: ", os.path.basename(fname))


# Check if Windows partition is writable, or read-only
def writable():
    mtab = open("/etc/mtab", "r")
    lines = mtab.read().split('\n')
    mtab.close()

    for line in lines:
        if "/dev/sda3 /Windows fuseblk rw" in line:
            return True
    return False


# Function that handles the actual file-transfers
def sync(lin_dir, MODE, QUIET):
    # Trim trailing slash from pathname, if present
    if lin_dir[-1] == "/":
        lin_dir = lin_dir[:-1]

    # Look for symbolic link to equivalent Windows partition directory
    winlink = lin_dir + "/Windows"
    if not os.path.exists(winlink):
        if not QUIET:
            print("Windows symlink not found :(\nExiting")
        exit(1)
        exit(1)

    # print(lin_dir)  # DEBUG
    os.chdir(lin_dir)
    lin_files = [f for f in os.listdir(lin_dir) if os.path.isfile(f)]

    os.chdir(winlink)
    win_dir = os.getcwd()
    win_files = [f for f in os.listdir(win_dir) if os.path.isfile(f)]
    os.chdir(lin_dir)

    # Evaluate Windows files (Pull mode)
    if (MODE == "pull") or (MODE == "both"):
        # print(lin_files)  # DEBUG
        for i in range(len(win_files)):
            file = win_files[i]
            win_file = win_dir + "/" + file

            # print(file)       # DEBUG
            if file in lin_files:
                lin_file = lin_dir + "/" + file
                win_time = int(os.path.getmtime(win_file))  # Round to whole sec
                lin_time = int(os.path.getmtime(lin_file))  # Round to whole sec

                # print(lin_time, "<->", win_time)    # DEBUG
                if lin_time >= win_time:
                    # Linux file more recent; remove from Windows file list
                    win_files[i] = None

    # Evaluate Linux files (Push mode)
    if (MODE == "push") or (MODE == "both"):
        for i in range(len(lin_files)):
            file = lin_files[i]
            lin_file = lin_dir + "/" + file

            # Ignore hidden files
            if file[0] == ".":
                lin_files[i] = None

            if file in win_files:
                # If present in both, compare modification times and dates
                win_file = win_dir + "/" + file
                lin_time = int(os.path.getmtime(lin_file))  # Round to whole sec
                win_time = int(os.path.getmtime(win_file))  # Round to whole sec

                if win_time >= lin_time:
                    # Windows file more recent; remove from Linux file list
                    lin_files[i] = None
    count = 0
    errors = 0

    # Transfer files from Windows to Linux (Pull mode)
    if (MODE == "pull") or (MODE == "both"):
        for file in win_files:
            if (not file) or (file is None):
                continue

            win_file = win_dir + "/" + file
            lin_file = lin_dir + "/" + file
            if not QUIET:
                print(win_file, "-->", lin_file, "\n")
            try:
                sh.copy2(win_file, lin_file)
                count += 1
            except:
                if not QUIET:
                    print("Error: cannot transfer file")
                errors += 1

    # Transfer files from Linux to Windows (Push mode)
    if (MODE == "push") or (MODE == "both"):
        for file in lin_files:
            if (not file) or (file is None):
                continue

            print(file)
            lin_file = lin_dir + "/" + file
            win_file = win_dir + "/" + file
            if not QUIET:
                print(lin_file, "-->", win_file, "\n")
            try:
                sh.copy2(lin_file, win_file)
                count += 1
            except:
                if not QUIET:
                    print("Error: cannot transfer file")
                errors += 1

    if not QUIET:
        print("Transferred %d/%d files" % (count-errors, count))

    return


if __name__ == "__main__":
    exit(main())
