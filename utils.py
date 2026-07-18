import os
import configparser
import shutil
import zlib
import hashlib
import sys


from models import Repository, GytBlob, GytTree


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
    """Find the repo root (where .gyt is present) by rec traversing up the tree from the curr dir

    Args:
        path (default = .): curr dir or specific path
        required (default = True): if we definitely require the root

    Returns:
        str

    Raises:
        Exception: If no .gyt in the tree
    """
    realPath = os.path.realpath(path)

    # gytDir = os.path.join(realPath, ".gyt")
    gytDir = os.path.join(realPath, ".git")

    if os.path.exists(gytDir) and os.path.isdir(gytDir):
        return realPath

    splitPath = realPath.split("/")

    if len(splitPath) == 2:
        if required:
            raise Exception("no .gyt along the file tree")
        else:
            return None

    return repoFind(os.path.join("../", path))


def objectRead(repo: Repository, sha: str):

    objectFile = repoPath(repo, "objects", sha[:2], sha[2:])

    if not os.path.isfile(objectFile):
        return None

    with open(objectFile, "rb") as f:
        contentsRaw = zlib.decompress(f.read())

        firstSpaceIdx = contentsRaw.find(b" ")
        nullByteIdx = contentsRaw.find(b"\x00")

        if firstSpaceIdx == -1:
            raise Exception("No space")
        if nullByteIdx == -1:
            raise Exception("No null byte")

        # b'commit 18\x00hi my name is hari'
        objectType = contentsRaw[:firstSpaceIdx]
        objectSize = int(contentsRaw[firstSpaceIdx + 1 : nullByteIdx].decode("ascii"))

        if objectSize != len(contentsRaw) - nullByteIdx - 1:
            raise Exception(f"Malformed object {sha}: bad length")

        # TODO:Add the switch after we create the different objects
        currObject = contentsRaw[nullByteIdx + 1 :]

        match objectType:
            case b"blob":
                return GytBlob(currObject)
            case b"tree":
                treeObject = GytTree()
                treeObject.deserialize(currObject)
                return treeObject

            case _:
                raise Exception("Not a proper Gyt Object type")


def objectWrite(repo: Repository | None, gytObject):
    """If repo is not None writes object into .gyt/objects or simply return hash.

    Args:
        gytObject : blob | tree | commit | hash
        repo: repos object

    Returns:
        str
    """
    byteData = gytObject.serialize()

    # b'commit 18\x00hi my name is hari'
    byteData = gytObject.type + b" " + str(len(byteData)).encode() + b"\x00" + byteData

    sha = hashlib.sha1(byteData).hexdigest()

    if repo:
        objectPath = repoFile(repo, "objects", sha[:2], sha[2:])
        compressedData = zlib.compress(byteData)

        with open(objectPath, "wb") as f:
            f.write(compressedData)
    return sha


def findObject(repo: Repository, objectId: str, objectType: bytes | None):
    """Find the object filename /hashid

    Args:
        repo: [TODO:description]
        objectId: [TODO:description]
        objectType: [TODO:description]

    Returns:
        [TODO:return]
    """
    return objectId


def catFile(repo: Repository, objectId: str, objectType: bytes | None):
    gytObject = objectRead(repo, findObject(repo, objectId, objectType))
    if gytObject:
        content = gytObject.serialize()
        if not content:
            raise Exception("object is empty no content")

        sys.stdout.buffer.write(content + b"\n")
    else:
        raise Exception(
            "No object in .gyt/objects dir with the hashid ,check the id or it might be a dir and not a file"
        )


def getGytObject(objectType: bytes, data: bytes):
    """Get the gytObject based on type

    Args:
        objectType: type of obj
        data: content of obj

    Returns:
        A subclass of GytObject

    Raises:
        Exception: invalid object type
    """
    match objectType:
        case b"blob":
            return GytBlob(data)
        case _:
            raise Exception(f"Not a valid Gyt Object type : {objectType}")


def hashObject(repo: Repository | None, objectType: bytes, data: bytes):
    gytObject = getGytObject(objectType, data)

    objectHash = objectWrite(repo, gytObject).encode()
    sys.stdout.buffer.write(objectHash + b"\n")


def lsTreeContent(repo: Repository, hashId: str, rec: bool = False, path: str = ""):
    objectName = findObject(repo, hashId, b"tree")
    currObject = objectRead(repo, objectName)

    if isinstance(currObject, GytBlob) or currObject is None:
        return

    for entry in currObject.items:
        if entry.type == "tree" and rec:
            newPath = entry.path if path == "" else path + f"/{entry.path}"
            lsTreeContent(repo, entry.sha, rec, newPath)
        else:
            finalPath = entry.path if path == "" else path + f"/{entry.path}"
            print(f"{entry.mode} {entry.type} {entry.sha} {finalPath}")
