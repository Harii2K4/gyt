import argparse
import sys
import os

from utils import (
    Repository,
    catFile,
    hashObject,
    lsTreeContent,
    repoCreate,
    repoFind,
    repoRemove,
)


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


def cmdCatFile(args: argparse.Namespace):
    repoRoot = repoFind(".")
    if not repoRoot:
        raise Exception("Not in a gyt repo , use init to instialise")

    catFile(Repository(repoRoot), args.objectid, args.type.encode())


def cmdHashObject(args: argparse.Namespace):
    repoRoot = repoFind()
    objectPath = os.path.realpath(args.path)

    if repoRoot is None:
        raise Exception(
            "Not in gyt repo either use gyt init to create one or do not pass -w"
        )

    if repoRoot not in os.path.realpath(args.path):
        raise Exception(f"Object path {objectPath} not in gyt repo {repoRoot}")

    if not os.path.exists(objectPath):
        raise Exception(f"The path {objectPath} doesnt exist ")

    if args.write:
        repo = Repository(repoRoot)
    else:
        repo = None

    if args.checkIpBuffer:
        contents = sys.stdin.buffer.read()
        objectType = b"blob"

    else:
        if args.path == "":
            raise Exception("Object path is '' , enter a proper object path")
        with open(args.path, "rb") as f:
            contents = f.read()

        objectType = args.type.encode()
        if objectType == b"":
            if os.path.isdir(objectPath):
                objectType = b"tree"
            elif os.path.isfile(objectPath):
                objectType = b"blob"
            else:
                raise Exception(f"{objectType} is not a valid Gyt type")

    hashObject(repo, objectType, contents)


def cmdLsTree(args: argparse.Namespace):
    repoRoot = repoFind()
    if repoRoot:
        repo = Repository(repoRoot)
        lsTreeContent(repo, args.hashid[0], rec=args.isRec)
    else:
        raise Exception("Not in a gyt repo")


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

    arsp = argSubParser.add_parser(
        "cat-file", help="Get print the contents of git object"
    )
    arsp.add_argument(
        "type",
        metavar="type",
        nargs="?",
        choices=["blob", "commit", "tag", "tree"],
        type=str,
        default="",
        help="type of gyt object can be blob , commit , tree or tag",
    )

    arsp.add_argument(
        "objectid",
        metavar="objectId",
        type=str,
        help="The Identifier for the object to display can be hash , branch , HEAD",
    )

    arsp = argSubParser.add_parser(
        "hash-object", help="Compute the hash Id and optionally store the object"
    )
    arsp.add_argument(
        "-w",
        dest="write",
        action="store_true",
        default=False,
        help="Whether to write object into gyt objects store ",
    )
    arsp.add_argument(
        "--stdin",
        dest="checkIpBuffer",
        action="store_true",
        default=False,
        help="To use the stdin buffer as content for the object",
    )

    arsp.add_argument(
        "-t",
        metavar="type",
        dest="type",
        nargs="?",
        choices=["blob", "commit", "tag", "tree"],
        default="",
        type=str,
        help="type of gyt object can be blob , commit , tree or tag",
    )

    arsp.add_argument(
        "path",
        metavar="path",
        type=str,
        nargs="?",
        default="",
        help="Path to the content to read into object",
    )

    arsp = argSubParser.add_parser("ls-tree", help="view the contents of a gyt tree")
    arsp.add_argument(
        "hashid",
        metavar="tree",
        type=str,
        nargs=1,
        default="",
        help="The sha1 id of the tree",
    )
    arsp.add_argument(
        "-r",
        dest="isRec",
        action="store_true",
        default=False,
        help="Whether to recursively display the directory contents",
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
            case "cat-file":
                cmdCatFile(args)
            case "hash-object":
                cmdHashObject(args)
            case "ls-tree":
                cmdLsTree(args)

    except Exception as e:
        print(e)
