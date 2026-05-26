from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def collect_json_results(results_dir: str | Path) -> list[dict[str, Any]]:
    directory = Path(results_dir)
    if not directory.exists():
        return []

    records = []
    for path in sorted(directory.rglob("*.json")):
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        records.append({"path": str(path), "data": data})
    return records


def write_summary(results_dir: str | Path, output_file: str | Path) -> dict[str, Any]:
    records = collect_json_results(results_dir)
    summary = {
        "results_dir": str(results_dir),
        "record_count": len(records),
        "files": [record["path"] for record in records],
    }
    with Path(output_file).open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, sort_keys=True)
    return summary


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Collect experiment JSON result files.")
    parser.add_argument("results_dir")
    parser.add_argument("--output", default="experiments/results/summaries/results_summary.json")
    args = parser.parse_args()
    summary = write_summary(args.results_dir, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
