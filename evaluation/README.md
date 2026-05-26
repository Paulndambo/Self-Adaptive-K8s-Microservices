# Evaluation

The evaluation package contains metric helpers, statistical comparison utilities, and report generation tools for comparing:

- adaptive controller
- HPA baseline
- PID baseline
- rule-based baseline

Generate a Markdown report from controller summary JSON:

```powershell
python evaluation/reports/generate_report.py experiments/results/processed/controller_summaries.json --output experiments/results/summaries/evaluation_report.md
```

The summary JSON can be either a list of controller summary objects or an object with a `summaries` field.
