# Workload Design

The initial workload target is Sock Shop. The repository includes lightweight local manifests and Python load generators for three traffic patterns.

## Workload Patterns

- Steady state: stable number of concurrent users.
- Flash crowd: low initial traffic followed by a sudden surge.
- Gradual ramp: traffic increases stepwise over time.

## Purpose

These patterns exercise different adaptation behaviors. Steady state measures stability and unnecessary scaling. Flash crowd measures reaction speed. Gradual ramp measures smoothness and proportionality.

## Output

Load tests emit JSON summaries with request count, success/failure count, average latency, p95 latency, and requests per second.
