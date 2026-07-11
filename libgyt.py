import argparse
import sys



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




def generateParse():
    argParser = argparse.ArgumentParser(
        prog="gyt",
        usage="Example usage is gyit init , gyt commit",
        description="Well this my git replica which is not as good as git for version control,it mostly for fun",
        epilog="Use gyt init to intialise gyt init your project",
    )

    argSubParser = argParser.add_subparsers(title="Commands", dest="command")
    argSubParser.required = True


    return argParser


def main(argv=sys.argv[1:]):
    argParser = generateParse()

    args = argParser.parse_args(argv)

