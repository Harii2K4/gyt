import os
import configparser
import shutil
import zlib
import hashlib


class Repository:
    gytDir: str = ""
    worktree: str = ""
    conf = None

    def __init__(self, path: str, force=False) -> None:
        self.worktree = path
        self.gytDir = os.path.join(path, ".gyt")

        if not (force or os.path.isdir(self.gytDir)):
            raise Exception(f"Not a Git repository {path}")

        # Read configuration file in .git/config
        self.conf = configparser.ConfigParser()
        cf = repoFile(self, "config")

        if cf and os.path.exists(cf):
            self.conf.read([cf])
        elif not force:
            raise Exception("Configuration file missing")

        if not force:
            vers = int(self.conf.get("core", "repositoryformatversion"))
            if vers != 0:
                raise Exception(f"Unsupported repositoryformatversion: {vers}")



def repoPath(repo: Repository, *path) -> str:
    """Returns the path under repo.gytDir

    Args:
        repo: Repository
        *path: path list

    Returns:
        str
    """
    return os.path.join(repo.gytDir, *path)


def repoFile(repo: Repository, *path) -> str:
    """Returns the git object file path

    Args:
        mkdir (default = False): Whether we create a new repo
        repo: Repo object
        *path: file path

    Returns:
       str|None
    """
    repoDir(repo, *path[:-1], mkdir=True)
    return repoPath(repo, *path)


def repoDir(repo: Repository, *path, mkdir=False) -> str | None:
    """Creates the dir for the repo if it doesnt exist

    Args:
        mkdir (default=False): Create the dir if doesnt
        repo: Repo instance
        *path: path of the repo

    Returns:
        str

    """
    path = repoPath(repo, *path)

    if os.path.exists(path):
        if os.path.isdir(path):
            return path
        else:
            raise Exception("Not a directory")
    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None


def getDefaultConfig() -> configparser.ConfigParser:
    """create intial gyt config

    Returns:
        configparser.ConfigParser
    """
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret


def repoCreate(path: str):
    """Create a repo with worktree and .gyt dir

    Args:
        path: repo path default is curr

    Raises:
        Exception: when not a dir or dir doesnt exist
    """
    repo = Repository(path, True)

    # do some dumb checks
    if os.path.exists(repo.worktree):
        if not os.path.isdir(repo.worktree):
            raise Exception(f"{path} is not a directory")
        if os.path.exists(repo.gytDir) and os.path.isdir(repo.gytDir):
            raise Exception(f"{path} already has a .gyt directory")
    else:
        os.makedirs(repo.worktree)

    assert repoDir(repo, "objects", mkdir=True)
    assert repoDir(repo, "refs", "heads", mkdir=True)
    assert repoDir(repo, "refs", "tags", mkdir=True)
    assert repoDir(repo, "branches", mkdir=True)

    with open(repoFile(repo, "description"), "w") as f:
        f.write(
            "Unnamed repository; edit this file 'description' to name the repository.\n"
        )
    with open(repoFile(repo, "HEAD"), "w") as f:
        f.write("ref: refs/heads/main\n")

    with open(repoFile(repo, "config"), "w") as f:
        config = getDefaultConfig()
        config.write(f)


def repoRemove(*path):
    """Used to remove the .gyt file from the repo
        *path: path to the repo root

    Raises:
        Exception: when no .gyt dir in the repo
    """
    repo = Repository(*path)

    if os.path.exists(repo.gytDir):
        if os.path.isdir(repo.gytDir):
            shutil.rmtree(repo.gytDir)
        else:
            raise Exception(".gyt is not a directory in this repo")

    else:
        raise Exception("Brother there is no .gyt in this directory")


def repoFind(path=".", required=True):

    realPath = os.path.realpath(path)

    gytDir = os.path.join(realPath, ".gyt")

    if os.path.exists(gytDir) and os.path.isdir(gytDir):
        return gytDir

    splitPath = realPath.split("/")

    if len(splitPath) == 2:
        if required:
            raise Exception("no .gyt along the file tree")
        else:
            return None

    return repoFind(os.path.join("../", path))
