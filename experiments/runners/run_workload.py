from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkloadCommand:
    name: str
    command: list[str]
    cwd: str | None = None


def run_workload_command(command: WorkloadCommand, timeout_seconds: int | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        command.command,
        cwd=command.cwd,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        check=False,
    )


def build_python_workload(path: str | Path) -> WorkloadCommand:
    workload_path = Path(path)
    return WorkloadCommand(
        name=workload_path.stem,
        command=["python", str(workload_path)],
        cwd=str(workload_path.parent),
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Run a workload generator script.")
    parser.add_argument("script", help="Path to a Python workload script.")
    args = parser.parse_args()
    result = run_workload_command(build_python_workload(args.script))
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
