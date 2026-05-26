# Minikube Setup

```powershell
minikube start --driver=docker --cpus=4 --memory=8192
minikube addons enable metrics-server
minikube addons enable ingress
kubectl apply -f kubernetes/namespaces/monitoring.yaml
kubectl apply -f workloads/sockshop/manifests/
```

For Prometheus, install `kube-prometheus-stack` with the values in `kubernetes/monitoring/prometheus-values.yaml`.
