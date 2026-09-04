"""Run the bounded Colorado experiment and persist private/raw and public outputs."""

import asyncio
from dataclasses import asdict
import json
from pathlib import Path

from app.research.experiment import public_summary, run_colorado_experiment


async def main() -> None:
    records, result = await run_colorado_experiment()
    repository_root = Path(__file__).parents[3]
    raw_path = repository_root / "data/research/colorado-owner-discovery-raw.json"
    summary_path = repository_root / "apps/api/app/research/results/colorado_owner_discovery_summary.json"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    # Raw records stay under ignored local data; only aggregate, non-identifying
    # measures are committed and served to the Research UI.
    raw_path.write_text(json.dumps([asdict(record) for record in records], default=str, indent=2) + "\n")
    summary_path.write_text(json.dumps(public_summary(result), indent=2) + "\n")
    print(json.dumps(public_summary(result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
