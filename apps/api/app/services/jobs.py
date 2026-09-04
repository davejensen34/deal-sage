from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Awaitable, Callable

@dataclass
class JobResult:
    name: str
    started_at: datetime
    finished_at: datetime
    success: bool
    detail: str | None = None

class JobRunner(ABC):
    @abstractmethod
    async def run(self, name: str, task: Callable[[], Awaitable[None]]) -> JobResult: ...

class InProcessJobRunner(JobRunner):
    async def run(self, name: str, task: Callable[[], Awaitable[None]]) -> JobResult:
        started=datetime.utcnow()
        try:
            await task(); return JobResult(name,started,datetime.utcnow(),True)
        except Exception as exc:
            return JobResult(name,started,datetime.utcnow(),False,str(exc))
