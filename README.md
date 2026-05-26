# Self-Adaptive Microservices

Research prototype for safe self-adaptation of Kubernetes-based microservice systems.

The project implements a MAPE-K controller that observes runtime metrics, detects performance or reliability issues, plans adaptation actions, validates them against hard safety constraints, optionally applies approved Kubernetes changes, records outcomes, and produces explanations. The core design principle is that AI-supported reasoning may explain or contextualize decisions, but it never directly controls Kubernetes or bypasses deterministic safety validation.

```text
monitor -> analyze -> plan -> safety -> execute -> knowledge -> reasoning
```

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Architecture](#architecture)
- [Safety Model](#safety-model)
- [Repository Layout](#repository-layout)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Running the Controller](#running-the-controller)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Workloads](#workloads)
- [Experiments](#experiments)
- [Evaluation](#evaluation)
- [Testing](#testing)
- [Observability and Stored Results](#observability-and-stored-results)
- [Research Notes](#research-notes)
- [Troubleshooting](#troubleshooting)

## What This Project Does

This repository contains a runnable prototype for evaluating self-adaptive microservice control in Kubernetes. It focuses on deployment scaling decisions and comparative experiments against conventional baselines.

Current capabilities include:

- Prometheus-backed metric collection for Kubernetes services.
- Analysis of CPU, memory, latency, throughput, error rate, readiness, missing metrics, and metric trends.
- Deterministic adaptation planning for scale-up, scale-down, no-op, and future configuration-change actions.
- Safety validation for replica bounds, total replica budget, cost budget, missing replica data, and cooldown-based anti-oscillation.
- Kubernetes execution adapter for scaling deployments through the Kubernetes Python client.
- JSONL-backed knowledge storage for metrics, plans, validation results, execution reports, policies, and scenario memory.
- Offline-safe reasoning and explanation layer, with injectable LLM clients for controlled experiments.
- Baseline controllers for HPA-style scaling, PID latency control, and rule-based scaling.
- Experiment runners, load generators, result collection utilities, statistics helpers, reports, and chart-ready summaries.
- Kubernetes manifests for controller RBAC, workloads, HPA baselines, Prometheus monitoring, and Grafana dashboard configuration.

## Architecture

The controller is implemented under `src/adaptive_controller` and is split into explicit phases:

| Layer | Package | Responsibility |
| --- | --- | --- |
| Monitor | `adaptive_controller.monitor` | Query Prometheus for service metrics and represent unavailable metrics safely. |
| Analyze | `adaptive_controller.analyze` | Convert metric snapshots into findings such as high CPU, SLA violation, low throughput, readiness issues, or trend changes. |
| Plan | `adaptive_controller.plan` | Produce deterministic adaptation plans from analysis findings. |
| Safety | `adaptive_controller.safety` | Approve or reject plans using hard constraints before execution. |
| Execute | `adaptive_controller.execute` | Apply approved changes to Kubernetes deployments. |
| Knowledge | `adaptive_controller.knowledge` | Persist metrics, plans, validations, executions, policy data, and scenario context. |
| Reasoning | `adaptive_controller.reasoning` | Retrieve context and generate explanations without actuator authority. |
| Baselines | `adaptive_controller.baselines` | Provide HPA, PID, and rule-based comparison controllers. |
| Observability | `adaptive_controller.observability` | Write trace, decision, and audit logs as JSONL. |

The orchestration point is `adaptive_controller.core.ControlLoop`. A single control-loop run returns a structured `ControlLoopResult` containing the run metadata, collected metrics, analysis report, plan batch, validation report, optional execution report, and generated explanation.

More detailed architecture notes live in:

- `docs/architecture/system-overview.md`
- `docs/architecture/mape-k-design.md`
- `docs/architecture/safety-validator.md`
- `docs/architecture/kubernetes-execution-layer.md`
- `docs/architecture/llm-reasoning-layer.md`

Draw.io diagrams are available in `docs/diagrams`.

## Safety Model

The LLM is never the actuator.

The main safety boundary is:

```text
AI explains or suggests
        |
Safety validator enforces hard constraints
        |
Deterministic executor applies approved action
        |
Knowledge store records outcome
```

The safety validator rejects unsafe plans before execution. Enforced checks include:

- Scaling plans must include current and target replica counts.
- Target replicas must stay above `MIN_REPLICAS`.
- Target replicas must stay below `MAX_REPLICAS`.
- Total replica count must stay below `MAX_TOTAL_REPLICAS`.
- Estimated replica cost must stay within `MAX_BUDGET_UNITS`.
- Services must respect `ADAPTATION_COOLDOWN_SECONDS` to reduce oscillation.

The default command-line entry point runs in dry-run mode. Kubernetes mutation only happens when a `ControlLoop` is constructed with `execute_actions=True` and a deployment executor is available.

## Repository Layout

```text
.
|-- data/                         # Seed metrics, incident scenarios, policy and budget data
|-- docs/                         # Architecture, experiment, metric, and diagram documentation
|-- evaluation/                   # Metric calculators, statistics helpers, report generation
|-- experiments/                  # Experiment configs, runners, notebooks, raw result examples
|-- infra/                        # Local cluster notes, kind config, Terraform placeholders
|-- kubernetes/                   # Controller, monitoring, namespace, and HPA manifests
|-- scripts/                      # Cluster setup, deploy, reset, and cleanup scripts
|-- src/adaptive_controller/       # Main Python package
|-- tests/                        # Unit and integration tests
|-- workloads/                    # Sock Shop and Online Boutique workload manifests and load tests
|-- .env.example                  # Environment variable template
|-- pyproject.toml                # Package metadata and pytest configuration
|-- requirements.txt              # Runtime and test dependencies
`-- README.md
```

## Requirements

For local dry runs and tests:

- Python 3.10 or newer.
- `pip`.

For Kubernetes experiments:

- `kubectl` configured for the target cluster.
- `kind` for `scripts/setup_cluster.sh`, or Minikube using `infra/local/minikube-setup.md`.
- `helm` for installing `kube-prometheus-stack`.
- A cluster that can run the workload manifests and expose Prometheus to the controller.

The Python package dependencies are:

- `httpx`
- `kubernetes`
- `pydantic`
- `PyYAML`
- `pytest`
- `pytest-mock`

## Quick Start

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the test suite:

```powershell
python -m pytest -p no:cacheprovider
```

Run one dry-run control-loop iteration:

```powershell
python -m adaptive_controller.main
```

By default, the controller reads settings from environment variables and does not execute Kubernetes changes.

## Configuration

Copy `.env.example` when you want a local environment file:

```powershell
Copy-Item .env.example .env
```

The application reads environment variables directly from the process environment. If you use a `.env` file, load it using your shell, editor, test runner, or deployment platform.

Important settings:

| Variable | Default | Purpose |
| --- | --- | --- |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus API endpoint. |
| `KUBERNETES_NAMESPACE` | `sockshop` | Namespace containing the target services. |
| `TARGET_SERVICES` | empty | Comma-separated service list. Example: `front-end,catalogue`. |
| `PROMETHEUS_QUERY_WINDOW` | `5m` | Prometheus range window used by metric queries. |
| `CPU_HIGH_THRESHOLD_CORES` | `0.8` | CPU threshold for high-utilization findings. |
| `LATENCY_P95_SLA_SECONDS` | `0.5` | p95 latency SLA threshold. |
| `ERROR_RATE_SLA_RPS` | `1.0` | Error-rate threshold. |
| `LOW_THROUGHPUT_RPS` | `1.0` | Low-throughput threshold. |
| `DEFAULT_CURRENT_REPLICAS` | `1` | Planner fallback when current replicas are not supplied. |
| `SCALE_STEP` | `1` | Replica increment or decrement for scaling plans. |
| `MIN_REPLICAS` | `1` | Lower safety bound for target replicas. |
| `MAX_REPLICAS` | `10` | Upper safety bound for a single service. |
| `MAX_TOTAL_REPLICAS` | `50` | Cluster-level safety budget. |
| `MAX_BUDGET_UNITS` | `50.0` | Cost budget used by the budget guard. |
| `ADAPTATION_COOLDOWN_SECONDS` | `300` | Cooldown window to reduce oscillation. |
| `KNOWLEDGE_STORAGE_DIR` | `experiments/results/raw/knowledge` | JSONL knowledge store path. |
| `REASONING_ENABLED` | `false` | Enables LLM-client calls when set to `true`. |
| `REASONING_PROVIDER` | `offline` | Reasoning provider label. |
| `REASONING_MODEL` | `offline-explainer` | Reasoning model label. |
| `OBSERVABILITY_ENABLED` | `true` | Enables trace, decision, and audit logs. |
| `OBSERVABILITY_LOG_DIR` | `experiments/results/raw/observability` | JSONL observability log path. |

Baseline settings such as `BASELINE_TARGET_CPU_CORES`, `BASELINE_TARGET_LATENCY_SECONDS`, and `PID_KP` tune the comparison controllers.

## Running the Controller

The simplest run is dry-run mode:

```powershell
python -m adaptive_controller.main
```

This constructs:

```python
ControlLoop(settings=load_settings(), execute_actions=False)
```

and prints the structured JSON result.

To execute Kubernetes scaling actions from custom code, create a `DeploymentExecutor`, pass it into `ControlLoop`, and set `execute_actions=True`. The executor only receives safety-approved plans.

```python
from adaptive_controller.config import load_settings
from adaptive_controller.core import ControlLoop
from adaptive_controller.execute import DeploymentExecutor, KubernetesClient

settings = load_settings()
executor = DeploymentExecutor(
    namespace=settings.monitor.namespace,
    kubernetes_client=KubernetesClient(),
)

result = ControlLoop(
    settings=settings,
    deployment_executor=executor,
    execute_actions=True,
).run_once()
```

Use dry-run mode for reproducible tests and experiments where mutation is not desired.

## Kubernetes Deployment

Create a local kind cluster:

```bash
./scripts/setup_cluster.sh
```

Deploy monitoring:

```bash
./scripts/deploy_monitoring.sh
```

Deploy the Sock Shop workload:

```bash
./scripts/deploy_workloads.sh
```

Deploy the adaptive controller manifests:

```bash
./scripts/deploy_controller.sh
```

Clean up:

```bash
./scripts/cleanup.sh
```

The controller service account, role, role binding, config map, and deployment manifests live in `kubernetes/controller`.

The executor requires permission to get, list, watch, patch, and update deployments and `deployments/scale` in the workload namespace.

## Workloads

### Sock Shop

Sock Shop manifests are in `workloads/sockshop/manifests`.

Load generators are dependency-light Python scripts:

```powershell
python workloads/sockshop/load-tests/steady_state.py --base-url http://localhost --duration-seconds 60 --users 50
python workloads/sockshop/load-tests/flash_crowd.py --base-url http://localhost --duration-seconds 300 --initial-users 50 --peak-users 500
python workloads/sockshop/load-tests/gradual_ramp.py --base-url http://localhost --duration-seconds 600 --initial-users 25 --peak-users 300
```

Use `--output-file` to write JSON summaries for later collection.

### Online Boutique

Online Boutique manifests are in `workloads/online-boutique/manifests`.

The included version is intentionally lightweight and uses representative service names with `hashicorp/http-echo` containers for local experiments:

- `frontend`
- `productcatalogservice`
- `cartservice`

Deploy manually:

```powershell
kubectl apply -f workloads/online-boutique/manifests/namespace.yaml
kubectl apply -f workloads/online-boutique/manifests/deployments.yaml
kubectl apply -f workloads/online-boutique/manifests/services.yaml
kubectl apply -f workloads/online-boutique/manifests/ingress.yaml
```

Run load tests:

```powershell
python workloads/online-boutique/load-tests/steady_state.py --base-url http://localhost --duration-seconds 60 --users 50
python workloads/online-boutique/load-tests/flash_crowd.py --base-url http://localhost --duration-seconds 300 --initial-users 50 --peak-users 500
python workloads/online-boutique/load-tests/gradual_ramp.py --base-url http://localhost --duration-seconds 600 --initial-users 25 --peak-users 300
```

## Experiments

Experiment configuration files live in `experiments/configs`.

Run the adaptive controller experiment:

```powershell
python experiments/runners/run_experiment.py experiments/configs/llm_adaptive_controller.yaml
```

The default adaptive experiment is still deterministic unless `REASONING_ENABLED=true` and a real LLM client is injected in code.

Load a baseline controller config:

```powershell
python experiments/runners/run_baseline.py experiments/configs/hpa_baseline.yaml
python experiments/runners/run_baseline.py experiments/configs/pid_controller.yaml
```

Run a workload script through the generic workload runner:

```powershell
python experiments/runners/run_workload.py workloads/sockshop/load-tests/steady_state.py
```

Collect JSON result files into a summary:

```powershell
python experiments/runners/collect_results.py experiments/results/raw --output experiments/results/summaries/results_summary.json
```

Experiment design notes are in:

- `docs/experiments/evaluation-plan.md`
- `docs/experiments/workload-design.md`
- `docs/experiments/metrics.md`
- `docs/experiments/baselines.md`

## Evaluation

The evaluation package compares:

- Adaptive controller.
- HPA baseline.
- PID baseline.
- Rule-based baseline.

Evaluation areas include:

- SLA violations.
- p95 latency.
- Resource usage.
- Scaling frequency.
- Adaptation latency.
- Stability and oscillation.
- Cost.

Generate a Markdown report from controller summary JSON:

```powershell
python evaluation/reports/generate_report.py experiments/results/processed/controller_summaries.json --output experiments/results/summaries/evaluation_report.md
```

Statistics helpers are available under `evaluation/statistics` for paired t-statistics, confidence intervals, effect size, and Bonferroni correction.

Metric helpers are available under `evaluation/metrics`.

## Testing

Run all tests:

```powershell
python -m pytest -p no:cacheprovider
```

Run a subset:

```powershell
python -m pytest tests/unit -p no:cacheprovider
python -m pytest tests/integration -p no:cacheprovider
```

The test suite covers controller phases, safety validation, planning, execution adapters, baselines, evaluation metrics, reports, documentation, Kubernetes manifests, load tests, and integration-level control-loop behavior.

## Observability and Stored Results

When observability is enabled, the controller writes JSONL logs to `experiments/results/raw/observability`:

- `trace.jsonl` records stage start, completion, and failure events.
- `decisions.jsonl` records analysis, plans, and validation decisions.
- `audit.jsonl` records safety validation and execution events.

The knowledge store writes JSONL records to `experiments/results/raw/knowledge`:

- `metrics.jsonl`
- `plans.jsonl`
- `validations.jsonl`
- execution records when execution is enabled

These files are useful for reproducibility, explanation, and downstream evaluation.

## Research Notes

This project is built around a conservative research claim:

> AI-supported reasoning can improve explainability and context awareness in self-adaptive microservice systems while preserving deterministic safety and reproducibility through explicit validation and execution boundaries.

The LLM reasoning layer is intentionally not an actuator. It can explain why deterministic components generated or rejected a plan, and it can retrieve context from the knowledge store, but it cannot scale workloads or override safety constraints.

The default offline reasoning mode keeps tests and experiments reproducible. Real LLM calls should be introduced only as a controlled experimental variable.

## Troubleshooting

### `ModuleNotFoundError: adaptive_controller`

Install dependencies from the project root or run commands from the repository root. `pyproject.toml` configures `src` as the package path for pytest.

```powershell
python -m pip install -r requirements.txt
```

### Prometheus queries fail

Check `PROMETHEUS_URL`, verify Prometheus is reachable, and confirm the ServiceMonitor has been applied:

```bash
kubectl get pods -n monitoring
kubectl get servicemonitor -A
```

### No services are monitored

Set `TARGET_SERVICES` or pass services explicitly to `ControlLoop.run_once`.

```powershell
$env:TARGET_SERVICES = "front-end"
python -m adaptive_controller.main
```

### Scaling does not happen

The default entry point is dry-run only. Real scaling requires all of the following:

- `execute_actions=True`.
- A configured `DeploymentExecutor`.
- Kubernetes credentials or in-cluster config.
- RBAC permission for deployments and `deployments/scale`.
- A plan approved by the safety validator.

### Safety rejects a plan

Inspect the validation report and `audit.jsonl`. Common causes are replica bounds, total replica budget, estimated cost budget, or cooldown violations.

### Load tests cannot reach the workload

Confirm ingress or port-forwarding is configured and pass the correct `--base-url` to the load generator.
