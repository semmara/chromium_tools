#!/usr/bin/env python
# pylint: disable=C0301

"""
Script to mirror chromium sources.
No need to modify depot_tools.
Prevent reaching quota.

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
import xml.etree.cElementTree as ET
import sys
if sys.version_info[0] < 3:
    from urllib import urlopen
else:
    from urllib.request import urlopen
from contextlib import closing


__author__ = "Rainer Semma"
__copyright__ = "Copyright (C) 2015 Rainer Semma"
__license__ = "Chocolateware"  # dark ;)
__version__ = "1.0"


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

    server = "https://chromium.googlesource.com/"

    parser = argparse.ArgumentParser()
    parser.add_argument('-C', "--directory", default='.')
    # TODO: parser.add_argument('-I', "--ignore", )
    args = parser.parse_args()

    print()
    print("Get a cup of coffee. This will take some time.")
    print()

    old_cwd = os.getcwd()
    try:
        os.chdir(args.directory)

        # read repos from web
        url = "https://chromium.googlesource.com/"
        with closing(urlopen(url)) as f:
            webdata = f.read()

        # catch available repos
        root = ET.fromstring(webdata)
        entries = [server+a.text+".git" for a in root.findall(".//tr/td/a[1]") if cmd_wrapper("git ls-remote --exit-code -h %s%s.git" % (server, a.text)) == 0]

        for repo in entries:
            print()
            print("-"*60)
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
