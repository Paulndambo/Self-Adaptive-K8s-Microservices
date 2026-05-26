# Safety Validator

The safety validator gates all adaptation plans before execution.

## Enforced Rules

- Scaling plans must include current and target replica counts.
- Target replicas must not fall below the configured minimum.
- Target replicas must not exceed the configured maximum.
- Total replicas must remain within the configured cluster budget.
- Estimated cost must remain within budget.
- Services must respect a cooldown window to reduce oscillation.

## Output

Validation produces a `ValidationReport` containing approved and rejected plans. Rejected plans include guard-specific reasons that are logged for auditability and explanation.

## Research Role

The safety layer is central to the research design. It allows AI-supported reasoning to exist in the architecture without giving the AI direct control over the system.
