# Live Kubernetes data collection

KubeNexus now reads cluster/workload metadata through the Python Kubernetes client and reads historical CPU/memory series through Prometheus. The integration is read-only. Recommendation analysis stays disabled until it is updated to derive its proposal from validated collected samples.

## Backend setup (Windows PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:KUBECONFIG = "$HOME\.kube\config"
$env:PROMETHEUS_URL = "http://localhost:9090"
python run.py
```

If `KUBECONFIG` is omitted, the Kubernetes client uses its normal default kubeconfig path. When KubeNexus runs inside a Kubernetes Pod, it uses the Pod's service account instead. The backend must be able to reach the Kubernetes API and Prometheus URL. Do not put kubeconfig contents or tokens in the frontend or commit them to the repository.

The registration form uses the backend's active kubeconfig context. If an API endpoint is entered, it must match that context. Registration checks Kubernetes access and discovers workloads before saving the cluster.

## Required Kubernetes permissions

The configured identity needs read access to nodes, namespaces, pods, deployments, StatefulSets, DaemonSets, and Jobs across the namespaces KubeNexus should monitor. Use a read-only Role/ClusterRole and bind it only to the required identity. No Kubernetes write permission is needed for this data collection feature.

## Prometheus metrics

Configure `PROMETHEUS_URL` to a Prometheus HTTP API URL reachable from the backend (for example, `http://localhost:9090`). If the environment variable is absent, KubeNexus uses the URL in its saved Optimization Settings. The Prometheus instance must expose `container_cpu_usage_seconds_total` and `container_memory_working_set_bytes` with `namespace`, `pod`, `container`, and `image` labels, commonly supplied by kubelet/cAdvisor scraping.

`GET /api/v1/workloads/{id}/metrics?range=24h` queries Prometheus `query_range` for real samples and stores returned timestamped values in the `metric_samples` table. Supported ranges are minute, hour, and day durations, such as `1h`, `24h`, and `7d`. Prometheus must retain the requested period. An unavailable source or empty result is returned as an API error; it is not replaced with synthetic samples.

The backend's active kubeconfig context is used for each registered cluster in this prototype. This is intended for one configured cluster context at a time; multi-cluster context selection and credential management need a separate implementation.
