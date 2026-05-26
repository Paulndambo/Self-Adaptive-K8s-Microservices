#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f workloads/sockshop/manifests/namespace.yaml
kubectl apply -f workloads/sockshop/manifests/deployments.yaml
kubectl apply -f workloads/sockshop/manifests/services.yaml
kubectl apply -f workloads/sockshop/manifests/ingress.yaml

kubectl -n sockshop rollout status deployment/front-end
kubectl -n sockshop rollout status deployment/catalogue
kubectl -n sockshop rollout status deployment/carts
