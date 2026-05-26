from __future__ import annotations

import argparse

from load_generator import LoadStep, add_common_args, run_load_test, write_summary


def build_steps(
    duration_seconds: int,
    initial_users: int,
    peak_users: int,
    surge_after_seconds: int,
) -> list[LoadStep]:
    warmup = max(0, min(duration_seconds, surge_after_seconds))
    peak_duration = max(0, duration_seconds - warmup)
    steps = []
    if warmup:
        steps.append(LoadStep(duration_seconds=warmup, users=initial_users))
    if peak_duration:
        steps.append(LoadStep(duration_seconds=peak_duration, users=peak_users))
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a flash-crowd Sock Shop workload.")
    add_common_args(parser)
    parser.add_argument("--initial-users", type=int, default=50)
    parser.add_argument("--peak-users", type=int, default=500)
    parser.add_argument("--surge-after-seconds", type=int, default=60)
    args = parser.parse_args()

    summary = run_load_test(
        scenario="flash_crowd",
        base_url=args.base_url,
        steps=build_steps(
            duration_seconds=args.duration_seconds,
            initial_users=args.initial_users,
            peak_users=args.peak_users,
            surge_after_seconds=args.surge_after_seconds,
        ),
        request_timeout_seconds=args.request_timeout_seconds,
        think_time_seconds=args.think_time_seconds,
    )
    write_summary(summary, args.output_file)


if __name__ == "__main__":
    main()
