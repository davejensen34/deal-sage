from abc import ABC, abstractmethod


class EvidenceStorage(ABC):
    @abstractmethod
    def save(self, key: str, content: bytes) -> str: ...
    @abstractmethod
    def read(self, key: str) -> bytes: ...

    def read_bounded(self, key: str, max_bytes: int) -> bytes:
        """Reject oversized content; backends should bound the underlying read."""
        content = self.read(key)
        if len(content) > max_bytes:
            raise ValueError("Evidence exceeds the byte limit")
        return content
    @abstractmethod
    def delete(self, key: str) -> None: ...
