# Kubernetes Execution Layer

The execution layer applies approved adaptation plans to Kubernetes.

## Supported Action

The current executor supports deployment scaling through the Kubernetes scale subresource:

```text
patch_namespaced_deployment_scale(namespace, deployment, replicas)
```

## Required Permissions

The controller service account requires permission to get, list, watch, patch, and update deployments and `deployments/scale` in the workload namespace.

## Execution Contract

Only safety-approved plans are executed. Rejected plans are skipped and recorded. No-op plans are skipped cleanly. Execution results are returned as structured `ExecutionReport` objects and can be stored by the knowledge layer.
