#!/usr/bin/env python
# pylint: disable=C0301

"""
Script to mirror chromium sources.
No need to modify depot_tools.
Run the following commands to modify your global '.gitconfig' file:
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
import tempfile
import xml.etree.cElementTree as ET

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
    args = parser.parse_args()

    old_cwd = os.getcwd()
    try:
        os.chdir(args.directory)

        tmp_dir = tempfile.gettempdir()
        if os.path.isdir(os.path.join(tmp_dir, "manifest")):
            print("Existing 'manifest' found. Trying to update.")
            mani_cmd = "git -C %s pull" % os.path.join(tmp_dir, "manifest")
        else:
            print("Downloading 'manifest' to temp folder.")
            mani_cmd = "git -C %s clone https://chromium.googlesource.com/chromium/manifest.git" % tmp_dir
        if cmd_wrapper(mani_cmd) != 0:
            raise Exception("Error while downloading/updating 'manifest'")
        mani_tree = ET.parse(os.path.join(tmp_dir, 'manifest', 'default.xml'))
        mani_root = mani_tree.getroot()
        entries = ["https://chromium.googlesource.com/"+proj.get("name") for proj in mani_root.iter('project')]

        entries.append("https://chromium.googlesource.com/chromium/tools/depot_tools.git")

        entries.append("https://chromium.googlesource.com/chromium/reference_builds/chrome_mac.git")
        entries.append("https://chromium.googlesource.com/chromium/reference_builds/chrome_linux64.git")
        entries.append("https://chromium.googlesource.com/chromium/reference_builds/chrome_win.git")
        entries.append("https://chromium.googlesource.com/chromium/deps/swig/mac.git")
        entries.append("https://chromium.googlesource.com/chromium/deps/swig/win.git")

        entries.append("https://chromium.googlesource.com/chromium/buildtools.git")
        entries.append("https://chromium.googlesource.com/chromium/deps/xz.git")
        entries.append("https://chromium.googlesource.com/chromium/cdm.git")
        entries.append("https://chromium.googlesource.com/chromium/canvas_bench.git")

        print()
        print("Get a cup of coffee. This will take some time.")
        print()

        for repo in entries:
            print()
            print("-"*40)
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
