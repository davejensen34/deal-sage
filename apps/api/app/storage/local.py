from pathlib import Path
from .base import EvidenceStorage


class LocalEvidenceStorage(EvidenceStorage):
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if self.root not in path.parents:
            raise ValueError("Invalid evidence key")
        return path

    def save(self, key: str, content: bytes) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Evidence keys are content-addressed. Refuse a conflicting rewrite so a
        # later parser or run cannot silently alter the source artifact it cites.
        if path.exists():
            if path.read_bytes() != content:
                raise ValueError("Evidence key already contains different content")
            return str(path)
        path.write_bytes(content)
        return str(path)

    def read(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        self._path(key).unlink(missing_ok=True)
