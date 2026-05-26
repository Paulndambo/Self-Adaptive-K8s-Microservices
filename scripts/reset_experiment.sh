#!/usr/bin/env bash
set -euo pipefail

kubectl -n sockshop scale deployment/front-end --replicas=2
kubectl -n sockshop scale deployment/catalogue --replicas=1
kubectl -n sockshop scale deployment/carts --replicas=1

kubectl -n sockshop rollout status deployment/front-end
kubectl -n sockshop rollout status deployment/catalogue
kubectl -n sockshop rollout status deployment/carts
