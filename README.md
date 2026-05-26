# Self-Adaptive Microservices

This project implements a research prototype for safe self-adaptation of Kubernetes-based microservice systems.

The system follows a MAPE-K feedback loop:

```text
monitor -> analyze -> plan -> safety -> execute -> knowledge -> reasoning
```

The controller monitors runtime metrics, detects performance issues, proposes adaptation plans, validates them through hard safety constraints, optionally executes approved Kubernetes scaling actions, records outcomes, and generates explanations. The LLM reasoning layer is intentionally outside direct control: it can explain or suggest, but it cannot scale Kubernetes resources or bypass safety validation.

## Current Implementation

- Prometheus monitor layer
- Deterministic analyzers for CPU, latency, throughput, error rate, readiness, and trends
- Deterministic planner for scale-up, scale-down, and no-op plans
- Safety validator for replica limits, budget limits, and cooldown/anti-oscillation
- Kubernetes execution adapter for deployment scaling
- JSONL-backed knowledge store
- Offline-safe reasoning/explanation layer
- HPA, PID, and rule-based baselines
- Evaluation metrics, statistics, reports, and chart-ready summaries
- Experiment runners and Sock Shop load-test scripts
- Kubernetes manifests and local deployment scripts
- Observability logs for traces, decisions, safety validation, and execution

## Run Tests

```powershell
python -m pytest -p no:cacheprovider
```

## Run One Dry-Run Control Loop

```powershell
python -m adaptive_controller.main
```

By default this does not execute Kubernetes changes. Real execution requires Kubernetes credentials and `execute_actions=True` when constructing the control loop.

## Research Principle

The LLM is never the actuator. The safe control path is:

```text
LLM explains or suggests
        |
Safety validator checks hard constraints
        |
Deterministic executor applies approved action
        |
Knowledge store records outcome
```
