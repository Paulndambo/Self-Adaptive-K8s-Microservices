# Evaluation Plan

The evaluation compares the adaptive controller against HPA, PID, and rule-based baselines under steady-state, flash-crowd, and gradual-ramp workloads.

## Procedure

1. Deploy the workload and monitoring stack.
2. Run one controller configuration per experiment.
3. Apply the same workload pattern to each controller.
4. Collect raw metrics, decisions, validation reports, execution reports, and load-test summaries.
5. Compute evaluation metrics.
6. Generate comparison tables and chart-ready summaries.

## Statistical Analysis

The statistics helpers support paired t-statistics, confidence intervals, effect size, and Bonferroni correction. Repeated trials should be used before making claims about performance improvement.

## Expected Research Questions

- Does the adaptive controller reduce SLA violations compared with baselines?
- Does it avoid unnecessary scaling?
- Does safety validation reduce unstable or unsafe actions?
- Does the reasoning layer improve explainability without compromising deterministic control?
