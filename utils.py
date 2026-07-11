import os
import configparser
import shutil


class Repository:
    gytDir: str = ""
    worktree: str = ""
    conf: str = ""

    def __init__(self, path: str, force=False) -> None:
        self.worktree = path
        self.gytDir = os.path.join(path, ".gyt")


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
    ret = configparser.ConfigParser()

    ret.add_section("core")
    ret.set("core", "repositoryformatversion", "0")
    ret.set("core", "filemode", "false")
    ret.set("core", "bare", "false")

    return ret


def repoCreate(path: str):

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
    repo = Repository(*path)

    if os.path.exists(repo.gytDir):
        if os.path.isdir(repo.gytDir):
            shutil.rmtree(repo.gytDir)
        else:
            raise Exception(".gyt is not a directory in this repo")

    else:
        raise Exception("Brother there is no .gyt in this directory")
