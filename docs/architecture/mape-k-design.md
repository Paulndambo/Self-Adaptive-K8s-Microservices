# MAPE-K Design

The controller follows the MAPE-K model: Monitor, Analyze, Plan, Execute, and Knowledge.

## Monitor

The monitor layer queries Prometheus for service metrics such as CPU usage, memory usage, request rate, error rate, p95 latency, replica counts, and pod readiness. Missing metrics are represented as unavailable values instead of crashing the control loop.

## Analyze

The analyze layer converts raw metric snapshots into findings. It detects threshold violations, SLA violations, metric trends, missing signals, and unhealthy pod readiness.

## Plan

The plan layer maps findings to proposed adaptation plans. Current actions include scale up, scale down, and no-op. Planning remains deterministic and does not apply changes.

## Execute

The execute layer applies only safety-approved plans. It uses the Kubernetes Python client to patch deployment scale subresources.

## Knowledge

The knowledge layer records metrics, plans, validations, executions, policies, scenarios, and text context. This supports reproducibility, later reasoning, and experimental analysis.

## Control Loop Boundary

Each phase has a typed input and output. This separation makes it possible to test components independently and compare the adaptive controller with baseline controllers.
