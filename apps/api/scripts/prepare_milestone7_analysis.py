"""Freeze requests offline using read-only SQLite and existing evidence files."""

import argparse
from hashlib import sha256
from pathlib import Path
import sqlite3

from app.research.analysis_preparation import canonical_bytes, prepare_bundle


def contained_file(root: Path, name: str) -> Path:
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError("Evidence path must remain inside its supplied root")
    return path


def prepare(manifest: Path, database: Path, evidence_dir: Path) -> dict:
    # mode=ro cannot create an absent database or change the research corpus.
    with sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")

        def load(packet):
            row = db.execute(
                "SELECT e.case_id,e.raw_artifact_id,e.content_hash,e.canonical_url,"
                "a.content_hash,a.canonical_url,a.storage_key,a.byte_size "
                "FROM case_evidence e JOIN raw_artifacts a ON a.id=e.raw_artifact_id WHERE e.id=?",
                (packet["evidence_id"],),
            ).fetchone()
            expected = (packet["case_id"], packet["artifact_id"], packet["raw_sha256"],
                        packet["url"], packet["raw_sha256"], packet["url"])
            if row is None or row[:6] != expected:
                raise ValueError("Evidence lineage mismatch")
            raw = contained_file(evidence_dir, row[6]).read_bytes()
            if len(raw) != row[7]:
                raise ValueError("Evidence byte count mismatch")
            text = contained_file(manifest.parent, packet["text_file"]).read_text(encoding="utf-8")
            return raw, text

        return prepare_bundle(manifest.read_bytes(), load)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    bundle = prepare(args.manifest, args.database, args.evidence_dir)
    payload = canonical_bytes(bundle)
    # Refuse overwrites: a later revision needs its own reviewable bundle.
    with args.output.open("xb") as stream:
        stream.write(payload)
    print(f"Prepared {len(bundle['requests'])} requests; SHA-256 {sha256(payload).hexdigest()}; not authorized")


if __name__ == "__main__":
    main()
