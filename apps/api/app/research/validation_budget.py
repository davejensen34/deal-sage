"""Durable reservations for the user's bounded M7 completion authorization."""

from contextlib import contextmanager
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path

from app.research.analysis_preparation import canonical_bytes

PROTOCOL = "m7-completion-v1"
CEILING_CENTS = 500


class ValidationBudget:
    """One session ledger includes failures and corrective attempts without refunds."""

    def __init__(self, directory: Path, approval: str):
        if approval != PROTOCOL:
            raise ValueError("Completion envelope approval required")
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.path = directory / "ledger.json"

    @contextmanager
    def locked(self):
        lock = self.directory / "session.lock"
        with lock.open("x"):
            pass
        try:
            yield self
        finally:
            lock.unlink()

    def read(self):
        if not self.path.exists():
            return {"protocol": PROTOCOL, "ceiling_cents": CEILING_CENTS, "attempts": []}
        record = json.loads(self.path.read_bytes())
        if record["protocol"] != PROTOCOL or record["ceiling_cents"] != CEILING_CENTS:
            raise ValueError("Budget identity changed")
        if any(type(r["reserved_cents"]) is not int or r["reserved_cents"] < 0 for r in record["attempts"]):
            raise ValueError("Invalid reservation history")
        if sum(r["reserved_cents"] for r in record["attempts"]) > CEILING_CENTS:
            raise ValueError("Budget already exceeded")
        for index, row in enumerate(record["attempts"], 1):
            if row["id"] != index or row["reserved_cents"] != {"search": 15, "analysis": 5, "http": 0}.get(row["kind"]):
                raise ValueError("Reservation history changed")
            request = self.directory / f"request-{index:03}.json"
            if sha256(request.read_bytes()).hexdigest() != row["request_sha256"]:
                raise ValueError("Reserved request changed")
            if row["status"] != "reserved":
                payload = (self.directory / f"result-{index:03}.json").read_bytes()
                if sha256(payload).hexdigest() != row["result_sha256"]:
                    raise ValueError("Finished result changed")
                estimated = json.loads(payload).get("estimated_usd")
                if estimated is not None and estimated * 100 > row["reserved_cents"]:
                    raise ValueError("Observed cost exceeded its reservation; reconcile before continuing")
        return record

    def save(self, record):
        temporary = self.directory / "ledger.tmp"
        with temporary.open("xb") as stream:
            stream.write(canonical_bytes(record))
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(self.path)

    def reserve(self, kind: str, request: dict, *, label: str):
        """Call while locked; persist request and reservation before external I/O."""
        costs = {"search": 15, "analysis": 5, "http": 0}
        if kind not in costs:
            raise ValueError("Unsupported validation action")
        record = self.read()
        if sum(r["reserved_cents"] for r in record["attempts"]) + costs[kind] > CEILING_CENTS:
            raise ValueError("Completion budget exhausted")
        if kind == "http" and sum(r["kind"] == "http" for r in record["attempts"]) >= 80:
            raise ValueError("Bounded HTTP request ceiling exhausted")
        attempt = len(record["attempts"]) + 1
        payload = canonical_bytes(request)
        with (self.directory / f"request-{attempt:03}.json").open("xb") as stream:
            stream.write(payload)
        row = {"id": attempt, "kind": kind, "label": label, "reserved_cents": costs[kind],
               "request_sha256": sha256(payload).hexdigest(), "status": "reserved",
               "started_at": datetime.now(timezone.utc).isoformat()}
        record["attempts"].append(row)
        self.save(record)
        return attempt

    def finish(self, attempt: int, result: dict):
        record = self.read()
        row = record["attempts"][attempt - 1]
        if row["id"] != attempt or row["status"] != "reserved":
            raise ValueError("Attempt is immutable once finished")
        payload = canonical_bytes(result)
        with (self.directory / f"result-{attempt:03}.json").open("xb") as stream:
            stream.write(payload)
        row.update(status=result["status"], result_sha256=sha256(payload).hexdigest(),
                   finished_at=datetime.now(timezone.utc).isoformat())
        self.save(record)
