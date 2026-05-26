#!/usr/bin/env bash
set -euo pipefail

RELEASE_NAME="${RELEASE_NAME:-kube-prometheus-stack}"
NAMESPACE="${NAMESPACE:-monitoring}"

kubectl apply -f kubernetes/namespaces/monitoring.yaml

if ! command -v helm >/dev/null 2>&1; then
  echo "helm is required to install kube-prometheus-stack." >&2
  exit 1
fi

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install "$RELEASE_NAME" prometheus-community/kube-prometheus-stack \
  --namespace "$NAMESPACE" \
  --values kubernetes/monitoring/prometheus-values.yaml

kubectl apply -f kubernetes/monitoring/servicemonitor.yaml
