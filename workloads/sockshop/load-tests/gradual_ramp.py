from __future__ import annotations

import argparse
import math

from load_generator import LoadStep, add_common_args, run_load_test, write_summary


def build_steps(
    duration_seconds: int,
    initial_users: int,
    peak_users: int,
    ramp_step_seconds: int,
) -> list[LoadStep]:
    if duration_seconds <= 0 or ramp_step_seconds <= 0:
        return []
    step_count = math.ceil(duration_seconds / ramp_step_seconds)
    steps = []
    for index in range(step_count):
        remaining = duration_seconds - (index * ramp_step_seconds)
        step_duration = min(ramp_step_seconds, remaining)
        if step_count == 1:
            users = peak_users
        else:
            ratio = index / (step_count - 1)
            users = round(initial_users + ((peak_users - initial_users) * ratio))
        steps.append(LoadStep(duration_seconds=step_duration, users=max(1, users)))
    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a gradual-ramp Sock Shop workload.")
    add_common_args(parser)
    parser.add_argument("--initial-users", type=int, default=25)
    parser.add_argument("--peak-users", type=int, default=300)
    parser.add_argument("--ramp-step-seconds", type=int, default=60)
    args = parser.parse_args()

    summary = run_load_test(
        scenario="gradual_ramp",
        base_url=args.base_url,
        steps=build_steps(
            duration_seconds=args.duration_seconds,
            initial_users=args.initial_users,
            peak_users=args.peak_users,
            ramp_step_seconds=args.ramp_step_seconds,
        ),
        request_timeout_seconds=args.request_timeout_seconds,
        think_time_seconds=args.think_time_seconds,
    )
    write_summary(summary, args.output_file)


if __name__ == "__main__":
    main()
