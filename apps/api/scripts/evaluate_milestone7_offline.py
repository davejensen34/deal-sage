"""Run from apps/api. This command has no live mode and never loads .env."""
import argparse
import json
from pathlib import Path
import sys

API_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API_ROOT))
import app.core.config as config

# Override configuration before importing services so even the unused global
# engine cannot select the operator's database or construct a provider.
settings = config.Settings(_env_file=None, database_url="sqlite:///:memory:",
    model_provider="disabled", web_search_provider="disabled", auth_mode="demo")
config.get_settings = lambda: settings
from app.research.transition_evaluation import run_cohort


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_cohort(API_ROOT / "tests/fixtures/milestone7_transition_cohort_v1.json")
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)
    raise SystemExit(0 if result["offline_contract_passed"] else 1)
