from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class MonitorSettings:
    prometheus_url: str = "http://localhost:9090"
    namespace: str = "sockshop"
    services: tuple[str, ...] = field(default_factory=tuple)
    query_timeout_seconds: float = 10.0
    query_window: str = "5m"


@dataclass(frozen=True)
class AnalyzerSettings:
    cpu_high_threshold_cores: float = 0.8
    memory_high_threshold_bytes: float = 512 * 1024 * 1024
    latency_p95_sla_seconds: float = 0.5
    error_rate_sla_rps: float = 1.0
    low_throughput_rps: float = 1.0
    trend_change_threshold_ratio: float = 0.15


@dataclass(frozen=True)
class PlannerSettings:
    default_current_replicas: int = 1
    scale_step: int = 1
    scale_up_confidence: float = 0.8
    scale_down_confidence: float = 0.6


@dataclass(frozen=True)
class SafetySettings:
    min_replicas: int = 1
    max_replicas: int = 10
    max_total_replicas: int = 50
    estimated_cost_per_replica: float = 1.0
    max_budget_units: float = 50.0
    cooldown_seconds: int = 300


@dataclass(frozen=True)
class KnowledgeSettings:
    storage_dir: str = "experiments/results/raw/knowledge"
    max_recent_items: int = 100


@dataclass(frozen=True)
class ReasoningSettings:
    enabled: bool = False
    provider: str = "offline"
    model: str = "offline-explainer"
    timeout_seconds: float = 30.0
    max_context_items: int = 5


@dataclass(frozen=True)
class BaselineSettings:
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_cores: float = 0.6
    target_latency_seconds: float = 0.5
    scale_tolerance_ratio: float = 0.10
    pid_kp: float = 1.0
    pid_ki: float = 0.0
    pid_kd: float = 0.0


@dataclass(frozen=True)
class ObservabilitySettings:
    log_dir: str = "experiments/results/raw/observability"
    enabled: bool = True


@dataclass(frozen=True)
class Settings:
    monitor: MonitorSettings = field(default_factory=MonitorSettings)
    analyzer: AnalyzerSettings = field(default_factory=AnalyzerSettings)
    planner: PlannerSettings = field(default_factory=PlannerSettings)
    safety: SafetySettings = field(default_factory=SafetySettings)
    knowledge: KnowledgeSettings = field(default_factory=KnowledgeSettings)
    reasoning: ReasoningSettings = field(default_factory=ReasoningSettings)
    baselines: BaselineSettings = field(default_factory=BaselineSettings)
    observability: ObservabilitySettings = field(default_factory=ObservabilitySettings)


def load_settings() -> Settings:
    services = tuple(
        item.strip()
        for item in os.getenv("TARGET_SERVICES", "").split(",")
        if item.strip()
    )
    monitor = MonitorSettings(
        prometheus_url=os.getenv("PROMETHEUS_URL", "http://localhost:9090"),
        namespace=os.getenv("KUBERNETES_NAMESPACE", "sockshop"),
        services=services,
        query_timeout_seconds=float(os.getenv("PROMETHEUS_TIMEOUT_SECONDS", "10")),
        query_window=os.getenv("PROMETHEUS_QUERY_WINDOW", "5m"),
    )
    analyzer = AnalyzerSettings(
        cpu_high_threshold_cores=float(os.getenv("CPU_HIGH_THRESHOLD_CORES", "0.8")),
        memory_high_threshold_bytes=float(os.getenv("MEMORY_HIGH_THRESHOLD_BYTES", str(512 * 1024 * 1024))),
        latency_p95_sla_seconds=float(os.getenv("LATENCY_P95_SLA_SECONDS", "0.5")),
        error_rate_sla_rps=float(os.getenv("ERROR_RATE_SLA_RPS", "1.0")),
        low_throughput_rps=float(os.getenv("LOW_THROUGHPUT_RPS", "1.0")),
        trend_change_threshold_ratio=float(os.getenv("TREND_CHANGE_THRESHOLD_RATIO", "0.15")),
    )
    planner = PlannerSettings(
        default_current_replicas=int(os.getenv("DEFAULT_CURRENT_REPLICAS", "1")),
        scale_step=int(os.getenv("SCALE_STEP", "1")),
        scale_up_confidence=float(os.getenv("SCALE_UP_CONFIDENCE", "0.8")),
        scale_down_confidence=float(os.getenv("SCALE_DOWN_CONFIDENCE", "0.6")),
    )
    safety = SafetySettings(
        min_replicas=int(os.getenv("MIN_REPLICAS", "1")),
        max_replicas=int(os.getenv("MAX_REPLICAS", "10")),
        max_total_replicas=int(os.getenv("MAX_TOTAL_REPLICAS", "50")),
        estimated_cost_per_replica=float(os.getenv("ESTIMATED_COST_PER_REPLICA", "1.0")),
        max_budget_units=float(os.getenv("MAX_BUDGET_UNITS", "50.0")),
        cooldown_seconds=int(os.getenv("ADAPTATION_COOLDOWN_SECONDS", "300")),
    )
    knowledge = KnowledgeSettings(
        storage_dir=os.getenv("KNOWLEDGE_STORAGE_DIR", "experiments/results/raw/knowledge"),
        max_recent_items=int(os.getenv("KNOWLEDGE_MAX_RECENT_ITEMS", "100")),
    )
    reasoning = ReasoningSettings(
        enabled=os.getenv("REASONING_ENABLED", "false").lower() == "true",
        provider=os.getenv("REASONING_PROVIDER", "offline"),
        model=os.getenv("REASONING_MODEL", "offline-explainer"),
        timeout_seconds=float(os.getenv("REASONING_TIMEOUT_SECONDS", "30")),
        max_context_items=int(os.getenv("REASONING_MAX_CONTEXT_ITEMS", "5")),
    )
    baselines = BaselineSettings(
        min_replicas=int(os.getenv("BASELINE_MIN_REPLICAS", "1")),
        max_replicas=int(os.getenv("BASELINE_MAX_REPLICAS", "10")),
        target_cpu_cores=float(os.getenv("BASELINE_TARGET_CPU_CORES", "0.6")),
        target_latency_seconds=float(os.getenv("BASELINE_TARGET_LATENCY_SECONDS", "0.5")),
        scale_tolerance_ratio=float(os.getenv("BASELINE_SCALE_TOLERANCE_RATIO", "0.10")),
        pid_kp=float(os.getenv("PID_KP", "1.0")),
        pid_ki=float(os.getenv("PID_KI", "0.0")),
        pid_kd=float(os.getenv("PID_KD", "0.0")),
    )
    observability = ObservabilitySettings(
        log_dir=os.getenv("OBSERVABILITY_LOG_DIR", "experiments/results/raw/observability"),
        enabled=os.getenv("OBSERVABILITY_ENABLED", "true").lower() == "true",
    )
    return Settings(
        monitor=monitor,
        analyzer=analyzer,
        planner=planner,
        safety=safety,
        knowledge=knowledge,
        reasoning=reasoning,
        baselines=baselines,
        observability=observability,
    )
