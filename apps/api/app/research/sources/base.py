from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SourceDefinition:
    key: str
    name: str
    jurisdiction: str
    source_type: str
    publisher: str
    landing_url: str
    api_url: str
    access_method: str
    license: str
    expected_refresh: str
    role_value: str
    limitations: tuple[str, ...]
    last_tested: str | None = None


@dataclass(frozen=True)
class SourceRecord:
    source_record_id: str
    canonical_url: str
    retrieved_at: datetime
    raw: dict[str, Any]


class SourceAdapter(ABC):
    definition: SourceDefinition

    @abstractmethod
    async def fetch_sample(self, limit: int) -> list[SourceRecord]: ...
