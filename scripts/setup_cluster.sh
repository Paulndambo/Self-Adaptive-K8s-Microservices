#!/usr/bin/env bash
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-adaptive-microservices}"

if ! command -v kind >/dev/null 2>&1; then
  echo "kind is required. Install kind or use infra/local/minikube-setup.md." >&2
  exit 1
fi

if ! kind get clusters | grep -qx "$CLUSTER_NAME"; then
  kind create cluster --config infra/local/kind-cluster.yaml
fi

kubectl apply -f kubernetes/namespaces/monitoring.yaml
kubectl apply -f kubernetes/namespaces/experiment.yaml
