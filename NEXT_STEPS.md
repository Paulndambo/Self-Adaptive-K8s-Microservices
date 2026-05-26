# NEXT_STEPS

Production-readiness roadmap for the Self-Adaptive Microservices prototype.

This document captures what is missing between the current research prototype and a production-ready adaptive control system for Kubernetes microservices. The prototype already demonstrates the core research idea: a MAPE-K control loop with deterministic safety validation and an explanation-oriented reasoning layer. The next step is to harden that idea into a reliable, secure, observable, Kubernetes-native control plane component.

## Production Readiness Goal

The target production system should be able to:

- Run continuously inside Kubernetes.
- Make repeatable adaptation decisions from trustworthy metrics.
- Enforce safety policies before any action is executed.
- Survive restarts, partial failures, and API outages.
- Produce clear audit trails for every decision.
- Avoid racing with humans, HPA, GitOps tools, or other controllers.
- Support controlled use of LLM reasoning without granting it actuator authority.
- Be deployable, testable, upgradeable, and observable like any other production platform service.

The safest framing is:

```text
reasoning may explain
policies must decide
executors may only apply approved actions
audits must record everything
```

## 1. Kubernetes-Native Controller or Operator

### Current Gap

The current project runs a control loop from Python code or experiment runners. That is useful for research and repeatable experiments, but production systems usually need a long-running Kubernetes-native controller.

### What To Build

Implement a controller/operator process that reconciles desired adaptive behavior against actual cluster state.

Important capabilities:

- Continuous reconcile loop.
- Leader election for high availability.
- Graceful shutdown on pod termination.
- Health, readiness, and startup probes.
- Idempotent reconciliation.
- Work queue with rate limiting.
- Backoff on failed operations.
- Namespace and service discovery.
- Ability to watch Kubernetes resources and trigger decisions.

### Implementation Direction

A Python implementation could use:

- Kubernetes Python client watches.
- A custom controller loop around `watch.Watch`.
- Lease-based leader election using Kubernetes `coordination.k8s.io/v1 Lease`.

Alternatively, a production-grade operator could be written in Go using:

- `controller-runtime`
- Kubebuilder
- CRDs for adaptive policies
- Built-in leader election and reconciliation patterns

### Example CRD Shape

```yaml
apiVersion: adaptive.example.io/v1alpha1
kind: AdaptiveServicePolicy
metadata:
  name: frontend-policy
  namespace: sockshop
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: front-end
  metrics:
    prometheusUrl: http://prometheus.monitoring:9090
    queryWindow: 5m
  objectives:
    maxP95LatencySeconds: 0.5
    maxErrorRateRps: 1.0
    targetCpuCores: 0.6
  safety:
    minReplicas: 1
    maxReplicas: 10
    cooldownSeconds: 300
    maxCostUnits: 50
  execution:
    mode: dryRun
```

### Example Controller Behavior

```text
watch AdaptiveServicePolicy
  -> collect metrics for targetRef
  -> analyze service health
  -> generate plan
  -> validate safety
  -> update status with decision
  -> execute only if mode is enabled and plan is approved
```

## 2. Robust Failure Handling

### Current Gap

The prototype handles some unavailable metrics safely, but production systems need clear behavior for many partial-failure cases.

### What To Build

Add explicit failure strategies for:

- Prometheus unavailable.
- Prometheus returning stale or incomplete data.
- Kubernetes API timeouts.
- Kubernetes API conflict errors.
- RBAC denial.
- Missing deployments.
- Failed scale patches.
- Controller restarts during cooldown.
- Corrupted or unavailable knowledge storage.
- Network partitions.

### Implementation Direction

Introduce a failure policy layer:

```python
class FailurePolicy:
    def should_use_last_known_good_metrics(self, error: Exception) -> bool:
        ...

    def should_skip_execution(self, validation_report) -> bool:
        ...

    def retry_budget_for(self, operation_name: str) -> RetryBudget:
        ...
```

Recommended behavior:

- Prefer no-op when data is stale or unavailable.
- Never scale from untrusted metrics.
- Retry transient Kubernetes errors with bounded exponential backoff.
- Treat RBAC errors as hard failures.
- Record every failure in audit logs and status fields.

### Usage Example

If Prometheus is unavailable:

```text
collect metrics -> failed
failure policy -> no-op decision
reasoning -> explain that metrics were unavailable
audit -> record skipped adaptation due to missing trustworthy signal
```

## 3. Production Policy Management

### Current Gap

Safety settings are currently loaded from environment variables and local files. Production teams need policy versioning, validation, ownership, and auditability.

### What To Build

Move safety and adaptation policies into managed resources.

Options:

- Kubernetes CRDs.
- ConfigMaps with strict schema validation.
- Open Policy Agent/Gatekeeper policies.
- Kyverno policies.
- A dedicated policy service.

### Implementation Direction

Add a policy schema and validation step before policies are accepted.

Example policy file:

```yaml
apiVersion: adaptive.example.io/v1alpha1
kind: SafetyPolicy
metadata:
  name: default-scaling-safety
spec:
  minReplicas: 1
  maxReplicas: 10
  maxTotalReplicas: 50
  cooldownSeconds: 300
  budget:
    estimatedCostPerReplica: 1.0
    maxBudgetUnits: 50.0
  freezeWindows:
    - name: business-hours-freeze
      timezone: Africa/Nairobi
      days: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
      start: "09:00"
      end: "17:00"
```

### Production Requirements

- Reject invalid policy before runtime.
- Store policy version with every decision.
- Record policy hash in audit logs.
- Support dry-run policy evaluation.
- Support policy rollback.

### Usage Example

```text
plan proposes front-end scale 4 -> 8
safety policy v12 validates maxReplicas=10
budget policy validates total cost
cooldown policy validates last action time
decision approved with policyVersion=v12
```

## 4. Security Hardening

### Current Gap

The prototype includes controller RBAC manifests, but production requires a broader security model.

### What To Build

Harden the complete deployment path:

- Least-privilege RBAC.
- Namespace-scoped permissions by default.
- Separate service accounts for reader, planner, and executor if split into services.
- Kubernetes Secrets for credentials.
- No secrets in logs, prompts, traces, or knowledge storage.
- NetworkPolicies for controller, Prometheus, and workload access.
- Container image scanning.
- Dependency scanning.
- Signed images.
- Read-only root filesystem.
- Non-root container user.
- Resource requests and limits.

### RBAC Example

The executor only needs permissions for target deployments and scale subresources:

```yaml
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments/scale"]
    verbs: ["get", "patch", "update"]
```

### NetworkPolicy Example

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: adaptive-controller-egress
  namespace: adaptive-controller
spec:
  podSelector:
    matchLabels:
      app: adaptive-controller
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
      ports:
        - protocol: TCP
          port: 9090
    - to:
        - namespaceSelector: {}
      ports:
        - protocol: TCP
          port: 443
```

## 5. High Availability

### Current Gap

The prototype can be deployed as a Kubernetes workload, but production availability requires careful handling when multiple replicas run.

### What To Build

Add:

- Leader election.
- Persistent cooldown state.
- Safe restart behavior.
- At-most-once execution semantics for scaling actions.
- Durable decision records.

### Implementation Direction

Use a Kubernetes Lease:

```text
controller replica A acquires lease
controller replica B waits
replica A reconciles policies and executes actions
if replica A dies, replica B acquires lease after timeout
```

Persist important state externally:

- Last action timestamp.
- Last approved plan.
- Last executed plan.
- Cooldown status.
- Policy version.
- Execution result.

### Storage Options

- Kubernetes CRD status fields.
- PostgreSQL.
- SQLite only for single-node local deployments.
- Object storage for experiment-only archives.

## 6. Durable State Management

### Current Gap

JSONL files are great for experiments, but production systems need stronger persistence guarantees.

### What To Build

Replace or supplement JSONL knowledge storage with durable storage.

Recommended records:

- Metric snapshots.
- Analysis findings.
- Plans.
- Validation decisions.
- Execution attempts.
- Rollbacks.
- Policy versions.
- Explanations.
- Human approvals.
- Incidents or operator annotations.

### Example Database Tables

```sql
CREATE TABLE adaptation_decisions (
  decision_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  service_name TEXT NOT NULL,
  action TEXT NOT NULL,
  current_replicas INTEGER,
  target_replicas INTEGER,
  validation_status TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL
);

CREATE TABLE execution_attempts (
  execution_id TEXT PRIMARY KEY,
  decision_id TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT,
  started_at TIMESTAMP NOT NULL,
  finished_at TIMESTAMP,
  FOREIGN KEY (decision_id) REFERENCES adaptation_decisions(decision_id)
);
```

### Usage Example

An SRE should be able to answer:

```text
Why did front-end scale from 3 to 5 at 13:42?
Which metric triggered it?
Which policy approved it?
Did execution succeed?
Was there a rollback?
What happened to latency afterward?
```

## 7. Full Observability

### Current Gap

The prototype writes useful JSONL traces, decisions, and audit logs. Production systems also need live controller metrics, dashboards, and alerts.

### What To Build

Expose Prometheus metrics from the controller:

- `adaptive_controller_reconcile_total`
- `adaptive_controller_reconcile_duration_seconds`
- `adaptive_controller_plan_total`
- `adaptive_controller_plan_approved_total`
- `adaptive_controller_plan_rejected_total`
- `adaptive_controller_execution_total`
- `adaptive_controller_execution_failed_total`
- `adaptive_controller_safety_rejection_total`
- `adaptive_controller_prometheus_query_failed_total`
- `adaptive_controller_kubernetes_api_error_total`
- `adaptive_controller_cooldown_active`
- `adaptive_controller_last_successful_run_timestamp`

### Example Metrics Endpoint

```python
from prometheus_client import Counter, Histogram, start_http_server

RECONCILE_TOTAL = Counter(
    "adaptive_controller_reconcile_total",
    "Number of reconcile attempts",
    ["namespace", "service"],
)

RECONCILE_DURATION = Histogram(
    "adaptive_controller_reconcile_duration_seconds",
    "Controller reconcile duration",
    ["namespace", "service"],
)

start_http_server(8080)
```

### Logging Requirements

Use structured logs with fields such as:

- `run_id`
- `decision_id`
- `namespace`
- `service`
- `stage`
- `policy_version`
- `action`
- `validation_status`
- `execution_status`

### Alert Examples

```text
Controller has not completed a successful run in 10 minutes.
Safety rejection rate is unusually high.
Kubernetes execution failures exceed 5% over 15 minutes.
Prometheus query failures exceed 10% over 15 minutes.
Controller is making repeated scale-up/scale-down decisions for the same service.
```

## 8. Safer Execution and Rollback

### Current Gap

The prototype can patch deployment scale subresources when execution is enabled. Production needs stronger pre-checks, post-checks, and rollback strategy.

### What To Build

Add:

- Pre-execution checks.
- Post-execution verification.
- Rollback executor.
- Timeout handling.
- Gradual execution mode.
- Change records.
- Optional approval gates.

### Pre-Execution Checks

Before scaling:

- Confirm deployment still exists.
- Confirm current replicas match plan assumptions.
- Confirm no conflicting rollout is active.
- Confirm cooldown still allows the action.
- Confirm policy version has not changed unexpectedly.

### Post-Execution Checks

After scaling:

- Confirm desired replica count changed.
- Confirm pods become ready.
- Confirm latency/error rate does not get worse after a grace period.
- Record success, degraded success, or failure.

### Rollback Example

```text
plan: scale front-end 3 -> 5
execution: successful patch
post-check: new pods fail readiness after 120 seconds
rollback: scale front-end 5 -> 3
audit: record rollback reason and final state
```

### Example API

```python
execution = executor.execute_approved(validation)
verification = verifier.verify(execution, timeout_seconds=180)

if verification.requires_rollback:
    rollback_report = rollback_executor.rollback(execution)
```

## 9. Concurrency Control

### Current Gap

Production clusters often have multiple actors changing the same deployment: humans, HPA, GitOps tools, CI/CD, and other controllers.

### What To Build

Add safeguards against:

- Overlapping control-loop runs.
- Duplicate scaling actions.
- Race conditions with HPA.
- Race conditions with manual `kubectl scale`.
- GitOps tools reverting runtime changes.
- Multiple controller instances targeting the same workload.

### Implementation Direction

Use optimistic concurrency checks:

```text
read deployment resourceVersion
build plan using current state
before execution, read deployment again
if resourceVersion or replicas changed unexpectedly, replan or skip
```

Use annotations to mark controller ownership:

```yaml
metadata:
  annotations:
    adaptive.example.io/managed: "true"
    adaptive.example.io/last-decision-id: "decision-123"
    adaptive.example.io/last-policy-version: "v12"
```

### HPA Interaction Modes

Choose one:

- Controller replaces HPA for selected workloads.
- Controller only recommends changes while HPA executes scaling.
- Controller adjusts HPA targets instead of deployment replicas.
- Controller refuses to manage workloads with active HPA unless explicitly allowed.

## 10. Human Approval and Change Management

### Current Gap

The prototype supports dry-run and execution modes, but production teams often need human approval for risky changes.

### What To Build

Add approval workflows:

- Auto-approve low-risk scale changes.
- Require approval for large scale changes.
- Require approval during business hours or freeze windows.
- Integrate with Slack, Microsoft Teams, Jira, ServiceNow, or GitHub issues.
- Support manual override and emergency stop.

### Example Approval Policy

```yaml
approval:
  autoApprove:
    maxReplicaDelta: 1
    allowedActions: ["scale_up"]
  requireApproval:
    maxReplicaDeltaGreaterThan: 2
    actions: ["scale_down", "config_change"]
  freezeWindows:
    - name: release-freeze
      start: "2026-06-01T00:00:00Z"
      end: "2026-06-07T23:59:59Z"
```

### Usage Example

```text
plan proposes scale cartservice 8 -> 3
safety approves
approval policy requires human approval for scale-down greater than 2 replicas
controller records pending approval
operator approves
executor applies action
```

## 11. Realistic Environment Validation

### Current Gap

The repository includes Sock Shop and a lightweight Online Boutique workload, which are useful for experiments. Production readiness needs broader validation.

### What To Build

Test against:

- Realistic traffic patterns.
- Multi-service dependencies.
- Multiple namespaces.
- Multiple clusters.
- Noisy neighbor scenarios.
- Pod churn.
- Node pressure.
- Rolling deployments.
- Prometheus outages.
- Network latency.
- Partial service failure.
- Workload-specific SLIs and SLOs.

### Experiment Examples

```text
steady-state traffic for 60 minutes
flash crowd with 10x traffic spike
gradual ramp for 2 hours
downstream service degradation
Prometheus unavailable for 5 minutes
Kubernetes API throttling
node CPU pressure
manual scale during active controller run
```

### Success Criteria

The system should:

- Avoid unsafe actions.
- Avoid oscillation.
- Improve or preserve SLA compliance.
- Use fewer resources than naive overprovisioning.
- Explain rejected and approved actions.
- Recover safely from failures.

## 12. LLM Governance

### Current Gap

The reasoning layer defaults to offline deterministic explanations, which is good for reproducibility. If real LLM calls are introduced, production governance is needed.

### What To Build

Add controls for:

- Prompt versioning.
- Prompt review.
- Context redaction.
- PII and secret filtering.
- Provider timeout handling.
- Provider fallback.
- Hallucination-resistant output formats.
- LLM response evaluation.
- Clear separation between explanation and execution.

### Hard Rule

The LLM must not directly produce executable Kubernetes actions.

Safer pattern:

```text
deterministic planner creates plan
safety validator approves/rejects
LLM receives read-only decision context
LLM produces explanation only
executor ignores LLM output
```

### Example Response Schema

```json
{
  "summary": "Scale-up was approved because p95 latency exceeded the configured SLA.",
  "evidence": [
    "latency_p95_seconds=0.82",
    "threshold=0.50",
    "target_replicas=4"
  ],
  "safety_notes": [
    "target replicas within maximum",
    "cooldown satisfied"
  ],
  "operator_notes": [
    "Review downstream cartservice if latency remains high after scaling."
  ]
}
```

### Governance Records

Store:

- Prompt template version.
- Model/provider.
- Input context hash.
- Redaction status.
- Response.
- Explanation ID.
- Decision ID.

## 13. Packaging and Deployment Maturity

### Current Gap

The project has Kubernetes manifests and scripts, but production deployment needs release engineering.

### What To Build

Add:

- Dockerfile.
- Helm chart or Kustomize overlays.
- Versioned container images.
- CI pipeline.
- Release tags.
- Image signing.
- SBOM generation.
- Dependency scanning.
- Upgrade notes.
- Configuration reference.

### Example Dockerfile Direction

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY pyproject.toml .
RUN pip install --no-cache-dir .

USER 10001
CMD ["python", "-m", "adaptive_controller.main"]
```

### Example Helm Values

```yaml
controller:
  image:
    repository: ghcr.io/example/adaptive-controller
    tag: 0.1.0
  replicas: 2
  leaderElection: true

prometheus:
  url: http://kube-prometheus-stack-prometheus.monitoring:9090

execution:
  mode: dryRun

safety:
  minReplicas: 1
  maxReplicas: 10
  cooldownSeconds: 300
```

## 14. Comprehensive Testing

### Current Gap

The repository has useful unit and integration tests. Production readiness requires broader test coverage and long-running validation.

### What To Build

Add test categories:

- Unit tests for every guard and planner.
- Contract tests for Prometheus query parsing.
- Contract tests for Kubernetes API interactions.
- End-to-end tests in kind or Minikube.
- Chaos tests for Prometheus and Kubernetes API outages.
- Load tests with realistic traffic.
- Soak tests over hours or days.
- Security tests.
- Policy validation tests.
- Upgrade tests.

### Example CI Stages

```text
lint
unit tests
integration tests
kind cluster e2e tests
container image build
image scan
Helm chart lint
policy validation
release artifact generation
```

### Example E2E Test

```text
create kind cluster
install Prometheus
deploy Sock Shop
deploy adaptive controller in dry-run mode
run flash-crowd load
assert plans are generated
assert safety validations are logged
assert no Kubernetes mutation happens in dry-run mode
enable execution in isolated namespace
assert approved scale-up changes deployment replicas
```

## 15. Multi-Objective Optimization

### Current Gap

The prototype focuses mainly on safe scaling decisions from performance signals. Production adaptation often balances multiple objectives.

### What To Build

Support policies and planners that consider:

- Latency.
- Error budget.
- Throughput.
- CPU.
- Memory.
- Cost.
- Carbon or energy usage.
- Availability.
- Service priority.
- Customer tier.
- Dependency impact.

### Example Objective Policy

```yaml
objectives:
  latency:
    p95Seconds: 0.5
    weight: 0.40
  cost:
    maxHourlyUnits: 100
    weight: 0.25
  stability:
    maxScalingEventsPerHour: 4
    weight: 0.20
  availability:
    minReadyRatio: 0.95
    weight: 0.15
```

### Planner Direction

The planner could rank candidate plans:

```text
candidate A: scale 3 -> 4, lower risk, moderate improvement
candidate B: scale 3 -> 6, higher cost, faster recovery
candidate C: no-op, safest, SLA likely remains violated
```

Then safety validation remains mandatory:

```text
planner ranks candidates
safety rejects unsafe candidates
executor applies only the best approved candidate
```

## Suggested Implementation Phases

### Phase 1: Production-Safe Dry Run

Goal: run continuously in Kubernetes without mutating workloads.

Build:

- Long-running controller process.
- Health probes.
- Prometheus metrics endpoint.
- Structured logs.
- CRD or ConfigMap policy loading.
- Status updates for decisions.
- Dry-run-only execution mode.

Outcome:

```text
Teams can deploy the controller and observe what it would do.
```

### Phase 2: Guarded Execution

Goal: enable low-risk scaling actions.

Build:

- Deployment executor wiring in production mode.
- Pre-checks and post-checks.
- Persistent cooldown state.
- RBAC hardening.
- Rollback support.
- Concurrency checks.

Outcome:

```text
The controller can safely apply approved scale-up or scale-down actions in a limited namespace.
```

### Phase 3: Operator Workflow

Goal: make adaptation explainable and manageable by humans.

Build:

- Approval workflow.
- Freeze windows.
- Decision history dashboard.
- Explanation review.
- Policy versioning.
- Incident annotations.

Outcome:

```text
SREs can understand, approve, reject, and audit adaptation decisions.
```

### Phase 4: Advanced Experiments and Optimization

Goal: expand research and production value.

Build:

- Multi-objective planner.
- More realistic workloads.
- Multi-cluster support.
- Controlled LLM provider integration.
- Extended statistical evaluation.
- Long-running comparative experiments.

Outcome:

```text
The system becomes a stronger platform for research and practical adaptive operations.
```

## Example Production Usage Scenarios

### Scenario 1: Dry-Run Recommendation Engine

A platform team deploys the controller with execution disabled:

```yaml
execution:
  mode: dryRun
```

The system observes services, generates plans, validates them, and explains what it would do. Engineers review the decision history before allowing live execution.

### Scenario 2: Low-Risk Auto Scaling

The controller is allowed to scale only one replica at a time:

```yaml
safety:
  minReplicas: 2
  maxReplicas: 8
  maxReplicaDelta: 1
  cooldownSeconds: 300
execution:
  mode: enabled
```

This is useful for services where HPA is too narrow because the team wants latency, error rate, and readiness signals included in the decision.

### Scenario 3: Human-Approved Scale Down

Scale-up is automatic, but scale-down requires approval:

```yaml
approval:
  autoApprove:
    actions: ["scale_up"]
  requireApproval:
    actions: ["scale_down"]
```

This protects availability while still allowing cost optimization through operator review.

### Scenario 4: Research Comparison

A researcher compares adaptive control against HPA, PID, and rule-based baselines:

```powershell
python experiments/runners/run_experiment.py experiments/configs/llm_adaptive_controller.yaml
python experiments/runners/run_baseline.py experiments/configs/hpa_baseline.yaml
python experiments/runners/run_baseline.py experiments/configs/pid_controller.yaml
python evaluation/reports/generate_report.py experiments/results/processed/controller_summaries.json --output experiments/results/summaries/evaluation_report.md
```

The output can support claims about SLA compliance, scaling stability, cost, and explainability.

## Definition of Production Ready

The system should not be considered production ready until it can demonstrate:

- Safe no-op behavior when metrics are missing or stale.
- Safe no-op behavior when policies are invalid.
- Safe no-op behavior when Kubernetes state changes unexpectedly.
- Durable decision and cooldown state across restarts.
- Auditable approval, validation, and execution records.
- Clear rollback behavior for failed adaptations.
- Least-privilege access to Kubernetes resources.
- Live metrics, logs, dashboards, and alerts.
- E2E tests in a real cluster environment.
- Documented operational procedures.
- Evidence from long-running load and failure experiments.

## Recommended Next PRs

1. Add a production-readiness issue template and roadmap labels.
2. Add a Dockerfile and build workflow.
3. Add controller self-metrics using `prometheus_client`.
4. Add a dry-run daemon mode that runs continuously on an interval.
5. Add persistent cooldown state outside in-memory execution.
6. Add pre-execution and post-execution checks.
7. Add Helm chart or Kustomize overlays.
8. Add a CRD proposal for adaptive service policies.
9. Add E2E tests using kind.
10. Add an operations guide for deploying in dry-run mode.

