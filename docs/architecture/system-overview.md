# System Overview

This system is a runtime architecture for self-managing cloud microservices. It observes Kubernetes workloads, detects performance or resource-management problems, plans safe adaptation actions, applies approved changes, and records outcomes for future analysis.

The prototype is organized as a deterministic control pipeline:

```text
monitor -> analyze -> plan -> safety -> execute -> knowledge -> reasoning
```

The primary adaptation action currently supported is Kubernetes deployment scaling. The design deliberately separates reasoning from execution: AI may support explanation and contextual interpretation, but deterministic safety checks decide whether a proposed action is allowed.

## Main Components

- `monitor`: reads metrics from Prometheus.
- `analyze`: identifies high CPU, high latency, low throughput, error-rate violations, unavailable metrics, readiness issues, and trends.
- `plan`: proposes adaptation plans such as scale up, scale down, or no-op.
- `safety`: enforces hard constraints before execution.
- `execute`: applies approved scaling actions through the Kubernetes API.
- `knowledge`: persists metrics, plans, validation results, executions, policies, and scenario context.
- `reasoning`: explains decisions and can later call an LLM, but cannot execute actions.
- `baselines`: provides HPA, PID, and rule-based controllers for comparison.
- `evaluation`: computes experiment metrics and generates reports.

## Architectural Claim

The research contribution is not simply adding AI to autoscaling. The stronger claim is that AI-supported reasoning can improve explainability and context awareness while preserving deterministic safety and reproducibility through explicit validation and execution boundaries.
