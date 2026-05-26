#!/usr/bin/env bash
set -euo pipefail

kubectl delete -f kubernetes/controller/deployment.yaml --ignore-not-found
kubectl delete -f kubernetes/controller/role-binding.yaml --ignore-not-found
kubectl delete -f kubernetes/controller/role.yaml --ignore-not-found
kubectl delete -f kubernetes/controller/configmap.yaml --ignore-not-found
kubectl delete -f kubernetes/controller/service-account.yaml --ignore-not-found
kubectl delete -f workloads/sockshop/manifests/ingress.yaml --ignore-not-found
kubectl delete -f workloads/sockshop/manifests/services.yaml --ignore-not-found
kubectl delete -f workloads/sockshop/manifests/deployments.yaml --ignore-not-found
kubectl delete -f workloads/sockshop/manifests/namespace.yaml --ignore-not-found
