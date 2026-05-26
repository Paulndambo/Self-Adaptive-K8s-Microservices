# Sock Shop Workload

This workload contains Kubernetes manifests and Python load-test scripts for the Sock Shop microservices demo.

The load tests are dependency-light and use Python's standard library:

```powershell
python workloads/sockshop/load-tests/steady_state.py --base-url http://localhost --duration-seconds 60 --users 50
python workloads/sockshop/load-tests/flash_crowd.py --base-url http://localhost --duration-seconds 300 --initial-users 50 --peak-users 500
python workloads/sockshop/load-tests/gradual_ramp.py --base-url http://localhost --duration-seconds 600 --initial-users 25 --peak-users 300
```

Use `--output-file` to write a JSON summary for experiment collection.
