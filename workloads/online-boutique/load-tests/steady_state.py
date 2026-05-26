from __future__ import annotations

import argparse

from load_generator import DEFAULT_PATHS, LoadStep, add_common_args, run_load_test, write_summary


def build_steps(duration_seconds: int, users: int) -> list[LoadStep]:
    return [LoadStep(duration_seconds=duration_seconds, users=users)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a steady-state Online Boutique workload.")
    add_common_args(parser)
    parser.add_argument("--users", type=int, default=50)
    args = parser.parse_args()

    summary = run_load_test(
        scenario="online_boutique_steady_state",
        base_url=args.base_url,
        steps=build_steps(args.duration_seconds, args.users),
        request_timeout_seconds=args.request_timeout_seconds,
        think_time_seconds=args.think_time_seconds,
        paths=DEFAULT_PATHS,
    )
    write_summary(summary, args.output_file)


if __name__ == "__main__":
    main()
