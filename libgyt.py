import argparse
import sys
import os

from utils import repoCreate, repoRemove


# from datetime import datetime
# from fnmatch import fnmatch
# import hashlib
# from math import ceil
# import zlib

try:
    import grp
    import pwd
except ModuleNotFoundError:
    pass


def cmdInit(args: argparse.Namespace):
    repoCreate(args.path)


def cmdRemove(args: argparse.Namespace):
    repoRemove(args.path)


def generateParse():
    argParser = argparse.ArgumentParser(
        prog="gyt",
        usage="Example usage is gyit init , gyt commit",
        description="Well this my git replica which is not as good as git for version control,it mostly for fun",
        epilog="Use gyt init to intialise gyt init your project",
    )

    argSubParser = argParser.add_subparsers(title="Commands", dest="command")
    argSubParser.required = True

    # Add the command parsers
    arsp = argSubParser.add_parser("init", help="Used to initialise the gyt repository")
    arsp.add_argument(
        "path",
        metavar="directory",
        default=".",
        nargs="?",
        help="Where to create the repo",
    )

    arsp = argSubParser.add_parser(
        "nuke", help="Used to remove the .gyt dir (can use rm -r .gyt also)"
    )
    arsp.add_argument(
        "path",
        metavar="directory",
        default=os.getcwd(),
        nargs="?",
        help="Where the .gyt is present to delete",
    )

    return argParser


def main(argv=sys.argv[1:]):
    argParser = generateParse()

    args = argParser.parse_args(argv)

    try:
        match args.command:
            case "init":
                cmdInit(args)
            case "nuke":
                cmdRemove(args)
    except Exception as e:
        print(e)
