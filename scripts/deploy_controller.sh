#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f kubernetes/namespaces/experiment.yaml
kubectl apply -f kubernetes/controller/service-account.yaml
kubectl apply -f kubernetes/controller/configmap.yaml
kubectl apply -f kubernetes/controller/role.yaml
kubectl apply -f kubernetes/controller/role-binding.yaml
kubectl apply -f kubernetes/controller/deployment.yaml

kubectl -n adaptive-controller rollout status deployment/adaptive-controller
