import os


class Repository:
    gytDir: str = ""
    worktree: str = ""
    conf = None

    def __init__(self, path: str, force=False) -> None:
        self.worktree = path
        self.gytDir = os.path.join(path, ".git")

        # if not (force or os.path.isdir(self.gytDir)):
        #     raise Exception(f"Not a Git repository {path}")
        #
        # # Read configuration file in .git/config
        # self.conf = configparser.ConfigParser()
        # cf = repoFile(self, "config")
        #
        # if cf and os.path.exists(cf):
        #     self.conf.read([cf])
        # elif not force:
        #     raise Exception("Configuration file missing")
        #
        # if not force:
        #     vers = int(self.conf.get("core", "repositoryformatversion"))
        #     if vers != 0:
        #         raise Exception(f"Unsupported repositoryformatversion: {vers}")


class GytObject:
    def __init__(self, data=None) -> None:
        if data is None:
            self.init()
        else:
            self.deserialize(data)

    def deserialize(self, data: bytes) -> str | None:
        raise Exception("Not implemented")

    def serialize(self, repo=None) -> bytes | None:
        raise Exception("Not implemented")

    def init(self) -> None:
        raise Exception("Not implemented")


class GytBlob(GytObject):
    type = b"blob"

    def deserialize(self, data):
        self.blobData = data

    def serialize(self, repo=None) -> bytes:
        return self.blobData


class GytCommit(GytObject):
    type = b"commit"

    def serialize(self, repo=None) -> bytes | None:
        return self.kvlmSerialize(self.kvlm)

    def deserialize(self, data: bytes) -> str | None:
        self.kvlm = self.kvlmParse(data)

    def init(self):
        self.kvlm = dict()

    def kvlmParse(self, raw: bytes) -> dict[bytes | None, list[bytes]]:
        keyValueMap = {}

        lines = raw.split(b"\n")
        idx = 0

        while idx < len(lines):
            currLine = lines[idx]

            if currLine == b"":
                body = lines[idx:]
                if None in keyValueMap:
                    keyValueMap[None].extend(body)
                else:
                    keyValueMap[None] = body
                break

            else:
                currLineSplit = currLine.split(b" ")
                key, values = currLineSplit[0], b" ".join(currLineSplit[1:])
                if key in keyValueMap:
                    keyValueMap[key].append(values)
                else:
                    keyValueMap[key] = [values]

                idx += 1

        return keyValueMap

    def kvlmSerialize(self, rawParsed: dict[bytes | None, list[bytes]]) -> bytes:
        rawSerialized = ""

        for key in rawParsed:
            values = rawParsed[key]
            try:
                if key is None:
                    rawSerialized += "\n".join([val.decode() for val in values])
                elif key:
                    for val in values:
                        rawSerialized += f"{key.decode()} {val.decode()}\n"
            except Exception as e:
                raise Exception(f"kvlm serialize Error: {e}")

        return rawSerialized.encode()


class GytTreeLeaf(object):
    def __init__(self, mode: bytes, path: str, sha: str) -> None:
        self.mode = mode
        self.path = path
        self.sha = sha
        self.type = "tree" if mode.startswith(b"04") else "blob"


class GytTree(GytObject):
    type = b"tree"

    def __init__(self) -> None:
        self.items = []

    def serialize(self, repo=None) -> bytes | None:
        return self.treeSerializer(self.items)

    def deserialize(self, data: bytes) -> str | None:
        self.items = self.parseTreeContent(data)

    def treeLeafSortKey(self, leaf: GytTreeLeaf):
        if leaf.mode.startswith(b"04"):
            return leaf.mode + b"/"
        else:
            return leaf.mode

    def treeSerializer(self, treeObjsList: list[GytTreeLeaf]) -> bytes:
        sortedTreeObjs = sorted(treeObjsList, key=self.treeLeafSortKey)
        treeData = b""

        for obj in sortedTreeObjs:
            treeData += (
                obj.mode
                + b" "
                + obj.path.encode("utf8")
                + b"\x00"
                + bytes.fromhex(obj.sha)
            )

        return treeData

    def parseTreeContent(self, rawTreeContent: bytes) -> list[GytTreeLeaf]:
        startIdx = 0
        treeObjects = []

        while startIdx < len(rawTreeContent):
            startIdx, currTreeObject = self.parseTreeEntry(startIdx, rawTreeContent)
            treeObjects.append(currTreeObject)

        return treeObjects

    def parseTreeEntry(
        self, idx: int, rawTreeContent: bytes
    ) -> tuple[int, GytTreeLeaf]:

        spaceIdx = rawTreeContent.find(b" ", idx)
        nullIdx = rawTreeContent.find(b"\x00", idx)

        mode = rawTreeContent[idx:spaceIdx]
        assert len(mode) == 5 or len(mode) == 6
        if len(mode) == 5:
            mode = b"0" + mode
        path = rawTreeContent[spaceIdx + 1 : nullIdx].decode()
        sha = bytes.hex(rawTreeContent[nullIdx + 1 : nullIdx + 21])

        return nullIdx + 21, GytTreeLeaf(mode, path, sha)
