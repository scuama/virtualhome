"""Archive Table 4 failures before rerunning them with the interface fix."""

from __future__ import annotations

import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results" / "table4"
MANIFEST = ROOT / "configs" / "table4" / "manifest.json"
ARCHIVE = RESULTS / "_attempts" / "pre_interface_fix"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    archived = 0
    preserved_successes = 0
    for item in manifest["runnable_configs"]:
        alias = item["model_alias"]
        scenario_id = item["source_scenario_id"]
        source = RESULTS / alias / scenario_id
        metrics_path = source / "metrics.json"
        if not metrics_path.exists():
            continue
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        if (
            metrics.get("run_status") == "complete"
            and bool(metrics.get("success", False))
        ):
            preserved_successes += 1
            continue
        destination = ARCHIVE / alias / scenario_id
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(source, destination)
            archived += 1
    print(
        f"Table 4 rerun preparation: archived={archived}; "
        f"preserved_successes={preserved_successes}"
    )


if __name__ == "__main__":
    main()
