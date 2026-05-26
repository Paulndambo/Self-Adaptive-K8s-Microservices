from __future__ import annotations

import argparse
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LoadStep:
    duration_seconds: int
    users: int


@dataclass
class RequestResult:
    status_code: int | None
    latency_seconds: float
    ok: bool
    error: str | None = None


@dataclass
class LoadTestSummary:
    scenario: str
    base_url: str
    duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_seconds: float
    p95_latency_seconds: float
    requests_per_second: float
    steps: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "scenario": self.scenario,
            "base_url": self.base_url,
            "duration_seconds": self.duration_seconds,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "average_latency_seconds": self.average_latency_seconds,
            "p95_latency_seconds": self.p95_latency_seconds,
            "requests_per_second": self.requests_per_second,
            "steps": self.steps,
        }


DEFAULT_PATHS = (
    "/",
    "/catalogue",
    "/category.html",
    "/cart",
    "/login",
)


def run_load_test(
    scenario: str,
    base_url: str,
    steps: list[LoadStep],
    request_timeout_seconds: float = 5.0,
    think_time_seconds: float = 1.0,
    paths: tuple[str, ...] = DEFAULT_PATHS,
    request_func: Callable[[str, float], RequestResult] | None = None,
) -> LoadTestSummary:
    request_func = request_func or perform_request
    started_at = time.monotonic()
    results: list[RequestResult] = []

    for step in steps:
        if step.duration_seconds <= 0 or step.users <= 0:
            continue
        results.extend(
            _run_step(
                base_url=base_url,
                step=step,
                paths=paths,
                request_timeout_seconds=request_timeout_seconds,
                think_time_seconds=think_time_seconds,
                request_func=request_func,
            )
        )

    elapsed = max(0.0, time.monotonic() - started_at)
    latencies = [result.latency_seconds for result in results]
    successful = sum(1 for result in results if result.ok)
    total = len(results)
    duration = sum(step.duration_seconds for step in steps)
    measured_duration = duration if duration > 0 else elapsed

    return LoadTestSummary(
        scenario=scenario,
        base_url=base_url,
        duration_seconds=duration,
        total_requests=total,
        successful_requests=successful,
        failed_requests=total - successful,
        average_latency_seconds=sum(latencies) / total if total else 0.0,
        p95_latency_seconds=percentile(latencies, 95),
        requests_per_second=total / measured_duration if measured_duration > 0 else 0.0,
        steps=[
            {"duration_seconds": step.duration_seconds, "users": step.users}
            for step in steps
        ],
    )


def _run_step(
    base_url: str,
    step: LoadStep,
    paths: tuple[str, ...],
    request_timeout_seconds: float,
    think_time_seconds: float,
    request_func: Callable[[str, float], RequestResult],
) -> list[RequestResult]:
    stop_at = time.monotonic() + step.duration_seconds
    results: list[RequestResult] = []
    lock = threading.Lock()

    def user_loop() -> None:
        local_random = random.Random()
        while time.monotonic() < stop_at:
            path = local_random.choice(paths)
            result = request_func(urljoin(base_url.rstrip("/") + "/", path.lstrip("/")), request_timeout_seconds)
            with lock:
                results.append(result)
            if think_time_seconds > 0:
                time.sleep(think_time_seconds)

    with ThreadPoolExecutor(max_workers=step.users) as executor:
        futures = [executor.submit(user_loop) for _ in range(step.users)]
        for future in as_completed(futures):
            future.result()
    return results


def perform_request(url: str, timeout_seconds: float) -> RequestResult:
    started_at = time.monotonic()
    request = Request(url, headers={"User-Agent": "adaptive-controller-load-test/0.1"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            status_code = int(response.status)
            response.read()
        latency = time.monotonic() - started_at
        return RequestResult(status_code=status_code, latency_seconds=latency, ok=200 <= status_code < 500)
    except HTTPError as exc:
        latency = time.monotonic() - started_at
        return RequestResult(status_code=exc.code, latency_seconds=latency, ok=False, error=str(exc))
    except URLError as exc:
        latency = time.monotonic() - started_at
        return RequestResult(status_code=None, latency_seconds=latency, ok=False, error=str(exc.reason))
    except TimeoutError as exc:
        latency = time.monotonic() - started_at
        return RequestResult(status_code=None, latency_seconds=latency, ok=False, error=str(exc))


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (percentile_value / 100) * (len(ordered) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def write_summary(summary: LoadTestSummary, output_file: str | Path | None) -> None:
    text = json.dumps(summary.to_dict(), indent=2, sort_keys=True)
    if output_file is None:
        print(text)
        return
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default="http://localhost", help="Sock Shop frontend base URL.")
    parser.add_argument("--duration-seconds", type=int, default=300)
    parser.add_argument("--request-timeout-seconds", type=float, default=5.0)
    parser.add_argument("--think-time-seconds", type=float, default=1.0)
    parser.add_argument("--output-file", default=None)
