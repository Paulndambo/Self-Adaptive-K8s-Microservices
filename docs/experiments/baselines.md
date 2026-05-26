# Baselines

The system includes three deterministic baselines for comparison.

## HPA Baseline

The HPA-style baseline scales replicas according to CPU usage relative to a target CPU value.

## PID Baseline

The PID baseline uses p95 latency error relative to a target latency value and applies proportional/integral/derivative control.

## Rule-Based Baseline

The rule-based baseline uses fixed conditions over CPU, latency, error rate, and throughput.

## Comparison Goal

The adaptive controller should be compared against these baselines on latency, resource usage, scaling frequency, adaptation latency, stability, and cost.
