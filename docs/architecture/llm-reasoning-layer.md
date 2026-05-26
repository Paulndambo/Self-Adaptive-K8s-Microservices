# LLM Reasoning Layer

The reasoning layer supports explanation and context retrieval. It does not directly control Kubernetes and does not bypass the safety validator.

## Responsibilities

- Build prompts from analysis findings, plans, safety validation results, and retrieved knowledge.
- Generate deterministic offline explanations when LLM access is disabled.
- Support injectable LLM clients for future provider integrations.
- Preserve the audit trail by explaining what the deterministic controller already decided.

## Safety Boundary

The LLM may explain why a plan was generated or why safety rejected it. It may also provide suggestions for future operator review. It must not directly apply changes, mutate Kubernetes resources, or override hard constraints.

## Default Mode

The default provider is `offline`, which keeps tests and experiments reproducible. Real LLM calls should be introduced as a controlled experimental variable.
