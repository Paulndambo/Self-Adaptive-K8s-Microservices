# Online Boutique Workload

This directory contains a lightweight local version of the Online Boutique workload for controller experiments.

The manifests use representative service names from Online Boutique:

- `frontend`
- `productcatalogservice`
- `cartservice`

For quick local experiments, these services use `hashicorp/http-echo` containers. They can be replaced later with the full Google Online Boutique manifests when higher workload realism is required.

## Deploy

```powershell
kubectl apply -f workloads/online-boutique/manifests/namespace.yaml
kubectl apply -f workloads/online-boutique/manifests/deployments.yaml
kubectl apply -f workloads/online-boutique/manifests/services.yaml
kubectl apply -f workloads/online-boutique/manifests/ingress.yaml
```

## Load Tests

```powershell
python workloads/online-boutique/load-tests/steady_state.py --base-url http://localhost --duration-seconds 60 --users 50
python workloads/online-boutique/load-tests/flash_crowd.py --base-url http://localhost --duration-seconds 300 --initial-users 50 --peak-users 500
python workloads/online-boutique/load-tests/gradual_ramp.py --base-url http://localhost --duration-seconds 600 --initial-users 25 --peak-users 300
```

Use `--output-file` to write JSON summaries for experiment collection.
