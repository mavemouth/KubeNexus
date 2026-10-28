KubeNexus live metrics and savings demo patch

Install: Stop the backend with Ctrl+C. From your KubeNexus project root, extract/copy these files and allow overwrite of the three matching paths under backend\app. Restart with your existing backend virtual environment and PROMETHEUS_URL=http://localhost:9090.

Demo-only path: In KubeNexus Settings, set Minimum Telemetry Observation Window to 0 days and save. This is only for a local classroom demonstration; do not use it for production recommendations. Short-window recommendations are labeled low confidence and medium risk. Estimated savings use illustrative rates ($0.04 per CPU core-hour and $0.005 per GB-hour), not your actual cloud invoice.

On the disposable kubenexus-demo Deployment, use moderately high requests such as 500m CPU and 512Mi memory, with limits 1000m CPU and 1Gi memory. After rollout, refresh the Workloads inventory. Open Inspect Details for kubenexus-demo, select 1h to collect recent Prometheus samples, then return to Workloads and refresh. Run Re-Analysis only after data quality changes to Valid. The local Minikube exercise itself does not create real cloud-bill savings.
