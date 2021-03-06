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
from HTMLParser import HTMLParser
import sys
if sys.version_info[0] < 3:
    from urllib import urlopen
else:
    from urllib.request import urlopen
from contextlib import closing
import json


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



class MyHTMLParser(HTMLParser):
    links = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.links.append(d["href"])


def main():
    """main function"""

    # default/const values
    server = "https://chromium.googlesource.com/"
    repo_list_fn = "repo_list.json"

    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-C', "--directory", help="change working directory", default='.')
    # TODO: parser.add_argument('-I', "--ignore", )
    parser.add_argument("--repo_list_fn", help="filename for repository-list", type=str, default=repo_list_fn)
    args = parser.parse_args()
    repo_list_fn = args.repo_list_fn

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
        hp = MyHTMLParser()
        hp.feed(webdata)
        hp.close()
        entries = [server+a[1:-1]+".git" for a in hp.links if cmd_wrapper("git ls-remote --exit-code -h %s%s.git" % (server, a[1:-1])) == 0]

        # save catched repos to file
        ent = {'entries':[{'repo':r} for r in entries]}
        if os.path.isfile(os.path.join(os.getcwd(), repo_list_fn)):
            with open(os.path.join(os.getcwd(), repo_list_fn), 'r') as f:
                file_data = f.read()
                try:
                    j_data = json.loads(file_data)
                    print("diff:", set(j_data) ^ set(ent))
                    ent.update(j_data)
                    print(ent)
                except:
                    pass
        else:
            print("no %s found" % repo_list_fn)
        with open(os.path.join(os.getcwd(), repo_list_fn), 'w') as f:
            json.dump(ent, f)
        # TODO: use ent

        # handling entries
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
