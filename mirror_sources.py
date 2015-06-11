#!/usr/bin/env python
# pylint: disable=C0301

"""
Script to mirror chromium sources.
No need to modify depot_tools.
Only run the following commands to modify you global .gitconfig file:
$ git config --global "url.<path/to/mirrors/>.insteadOf" "https://chromium.googlesource.com/"
$ git config --global --add "url.<path/to/mirrors/>.insteadOf" "https://chromium.googlesource.com/a/"
Replace '<path/to/mirrors/>' with your path.
"""

from __future__ import print_function
import os
import argparse
import subprocess as subp
import shlex
import shutil
from datetime import datetime

__author__ = "Rainer Semma"


def FileRead(filename, mode='rU'):
    """Source: http://src.chromium.org/svn/trunk/tools/depot_tools/gclient_utils.py"""
    with open(filename, mode=mode) as f:
        s = f.read()
        try:
            return s.decode('utf-8')
        except UnicodeDecodeError:
            return s


def cmd_wrapper(cmd):
    """subprocess wrapper"""
    print("Command:", cmd)
    rc = subp.Popen(shlex.split(cmd)).wait()
    if rc != 0:
        print("Error while running command.")
    print("Returncode:", rc)
    return rc


def main():
    """main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-C', "--directory", default='.')
    parser.add_argument('gclient_entries_file', help="'.gclient_entries' file")
    args = parser.parse_args()

    old_cwd = os.getcwd()
    try:
        os.chdir(args.directory)

        scope = {}
        exec(FileRead(args.gclient_entries_file), scope)

        print("Get a cup of coffee. This will take some time.")

        for _, src in scope["entries"].items():
            if '@' in src:
                repo = src.split('@')[0]  # TODO: check if second '@', e.g. git@...
            else:
                repo = src
            print("repo:", repo)
            subdir_repo = repo.split('/')[3:]
            subdir_repo_path = os.path.join(*subdir_repo)

            # try to update
            if os.path.isdir(subdir_repo_path):
                rc = cmd_wrapper("git -C %s remote update" % subdir_repo_path)
                if rc == 0:
                    continue

            # make subfolders if needed
            subdir = subdir_repo[:-1]
            if subdir:
                subdir = os.path.join(*subdir)
                if not os.path.isdir(subdir):
                    os.makedirs(subdir)
            else:
                subdir = '.'

            # move existing repo aside
            if os.path.exists(subdir_repo_path):
                appendix = datetime.today().isoformat()
                bak_name = os.path.basename(subdir_repo_path + "." + appendix + ".bak")
                shutil.move(subdir_repo_path, os.path.join(subdir, bak_name))

            # clone repo into subfolder
            cmd_wrapper("git -C %s clone --mirror %s" % (subdir, repo))
    finally:
        os.chdir(old_cwd)


if __name__ == '__main__':
    main()
