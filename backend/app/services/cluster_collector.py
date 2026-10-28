"""Read-only Kubernetes and Prometheus data collection for KubeNexus."""

from __future__ import annotations

import json
import hashlib
import math
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.models.schemas import Cluster, MetricTimeSeriesPoint, Workload


def _kubernetes_clients(
    auth_method: str = "local",
    kubeconfig_raw: str | None = None,
    bearer_token: str | None = None,
    api_endpoint: str | None = None
):
    try:
        from kubernetes import client, config
    except ImportError as exc:
        raise RuntimeError("Kubernetes support is not installed. Run: pip install -r backend/requirements.txt") from exc

    try:
        if auth_method == "kubeconfig" and kubeconfig_raw and kubeconfig_raw.strip():
            import yaml
            config_dict = yaml.safe_load(kubeconfig_raw)
            config.load_kube_config_from_dict(config_dict)
            return client.CoreV1Api(), client.AppsV1Api(), client.BatchV1Api(), client.VersionApi()

        elif auth_method == "token" and bearer_token and bearer_token.strip():
            if not api_endpoint or not api_endpoint.strip():
                raise RuntimeError("API Server Endpoint URL is required when authenticating with a Bearer Token.")
            configuration = client.Configuration()
            configuration.host = api_endpoint.rstrip("/")
            configuration.verify_ssl = False
            configuration.api_key = {"authorization": f"Bearer {bearer_token.strip()}"}
            api_client = client.ApiClient(configuration)
            return (
                client.CoreV1Api(api_client),
                client.AppsV1Api(api_client),
                client.BatchV1Api(api_client),
                client.VersionApi(api_client)
            )

        else:
            # Local / auto-detect mode (Minikube or in-cluster)
            kubeconfig = os.getenv("KUBECONFIG") or None
            if os.getenv("KUBERNETES_SERVICE_HOST"):
                config.load_incluster_config()
            else:
                config.load_kube_config(config_file=kubeconfig)
            return client.CoreV1Api(), client.AppsV1Api(), client.BatchV1Api(), client.VersionApi()

    except Exception as exc:
        raise RuntimeError(f"Could not load Kubernetes configuration ({auth_method}): {exc}") from exc


def _cpu_cores(value: str | None) -> float:
    if not value:
        return 0.0
    value = str(value)
    try:
        if value.endswith("n"):
            return float(value[:-1]) / 1_000_000_000
        if value.endswith("u"):
            return float(value[:-1]) / 1_000_000
        if value.endswith("m"):
            return float(value[:-1]) / 1000
        return float(value)
    except ValueError:
        return 0.0


def _memory_mb(value: str | None) -> float:
    if not value:
        return 0.0
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)([a-zA-Z]*)", str(value))
    if not match:
        return 0.0
    amount, unit = float(match.group(1)), match.group(2)
    factors = {"Ki": 1 / 1024, "Mi": 1, "Gi": 1024, "Ti": 1024 ** 2,
               "Pi": 1024 ** 3, "Ei": 1024 ** 4, "K": 1000 / 1024 / 1024,
               "M": 1000 / 1024, "G": 1000 ** 2 / 1024, "T": 1000 ** 3 / 1024,
               "P": 1000 ** 4 / 1024, "E": 1000 ** 5 / 1024, "": 1 / 1024 / 1024}
    return amount * factors.get(unit, 0)


def _fmt_cpu(cores: float) -> str:
    return f"{int(round(cores * 1000))}m" if cores < 1 else f"{cores:.2f} Cores"


class ClusterCollector:
    """Manages Kubernetes cluster connections and Prometheus metrics collection."""

    def verify(
        self,
        requested_endpoint: str | None = None,
        auth_method: str = "local",
        kubeconfig_raw: str | None = None,
        bearer_token: str | None = None
    ) -> dict[str, Any]:
        core, apps, batch, version_api = _kubernetes_clients(
            auth_method=auth_method,
            kubeconfig_raw=kubeconfig_raw,
            bearer_token=bearer_token,
            api_endpoint=requested_endpoint
        )
        try:
            version = version_api.get_code(_request_timeout=5)
            nodes = core.list_node(_request_timeout=5)
            core.list_namespace(limit=1, _request_timeout=5)
        except Exception as exc:
            raise RuntimeError(f"Kubernetes connection/access check failed: {exc}") from exc
        configuration = core.api_client.configuration
        actual_endpoint = (configuration.host or "").rstrip("/")
        if requested_endpoint and auth_method == "local":
            if requested_endpoint.rstrip("/") != actual_endpoint:
                is_local_req = "127.0.0.1" in requested_endpoint or "localhost" in requested_endpoint
                is_local_act = "127.0.0.1" in actual_endpoint or "localhost" in actual_endpoint
                if not (is_local_req and is_local_act):
                    raise RuntimeError("The entered API endpoint does not match the backend's active kubeconfig context.")
        elif not actual_endpoint and requested_endpoint:
            actual_endpoint = requested_endpoint
        return {
            "core": core,
            "apps": apps,
            "batch": batch,
            "endpoint": actual_endpoint,
            "version": getattr(version, "git_version", "unknown"),
            "node_count": len(nodes.items),
        }

    @staticmethod
    def _workload(cluster: Cluster, kind: str, obj: Any, core: Any) -> Workload:
        metadata, spec, status = obj.metadata, obj.spec, obj.status
        labels = getattr(getattr(spec, "selector", None), "match_labels", None) or {}
        selector_string = ",".join(f"{key}={value}" for key, value in labels.items())
        template = getattr(spec, "template", None)
        containers = getattr(getattr(template, "spec", None), "containers", []) or []
        cpu_request = sum(_cpu_cores((c.resources.requests or {}).get("cpu")) for c in containers if c.resources)
        cpu_limit = sum(_cpu_cores((c.resources.limits or {}).get("cpu")) for c in containers if c.resources)
        mem_request = sum(_memory_mb((c.resources.requests or {}).get("memory")) for c in containers if c.resources)
        mem_limit = sum(_memory_mb((c.resources.limits or {}).get("memory")) for c in containers if c.resources)
        replicas = int(getattr(spec, "replicas", 1) or 0)
        available = int(getattr(status, "available_replicas", 0) or 0)
        restarts = oom_kills = 0
        try:
            if kind == "Job":
                selector_string = f"job-name={name}"
            pods = core.list_namespaced_pod(metadata.namespace, label_selector=selector_string).items if selector_string else []
            for pod in pods:
                for container_status in (pod.status.container_statuses or []):
                    restarts += int(container_status.restart_count or 0)
                    state = container_status.last_state
                    if state and state.terminated and state.terminated.reason == "OOMKilled":
                        oom_kills += 1
        except Exception:
            # Workload metadata can still be shown when Pod-level read permission is absent.
            pass
        name, namespace = metadata.name, metadata.namespace
        stable_key = f"{cluster.id}:{namespace}:{kind.lower()}:{name}".encode("utf-8")
        stable_id = "workload-" + hashlib.sha256(stable_key).hexdigest()[:48]
        return Workload(
            id=stable_id, name=name, namespace=namespace,
            clusterId=cluster.id, clusterName=cluster.name, type=kind,
            replicasDesired=replicas, replicasAvailable=available,
            cpuRequest=_fmt_cpu(cpu_request), cpuLimit=_fmt_cpu(cpu_limit),
            cpuRequestCores=cpu_request, cpuLimitCores=cpu_limit, cpuUsageCores=0.0,
            memoryRequestMb=mem_request, memoryLimitMb=mem_limit,
            cpuUtilizationPct=0.0, memoryUtilizationPct=0.0,
            status="Healthy" if available >= replicas else "Warning",
            dataQualityStatus="insufficient_evidence", restarts=restarts,
            oomKills=oom_kills, throttlingCount=0, lastAnalysisTime="Not analyzed",
        )

    def discover(self, cluster: Cluster) -> list[Workload]:
        from app.storage.db import db
        creds = db.get_cluster_credentials(cluster.id)
        connection = self.verify(
            requested_endpoint=cluster.apiEndpoint,
            auth_method=creds.get("auth_method", "local"),
            kubeconfig_raw=creds.get("kubeconfig_raw"),
            bearer_token=creds.get("bearer_token")
        )
        core, apps, batch = connection["core"], connection["apps"], connection["batch"]
        result: list[Workload] = []
        try:
            for item in apps.list_deployment_for_all_namespaces().items:
                result.append(self._workload(cluster, "Deployment", item, core))
            for item in apps.list_stateful_set_for_all_namespaces().items:
                result.append(self._workload(cluster, "StatefulSet", item, core))
            for item in apps.list_daemon_set_for_all_namespaces().items:
                result.append(self._workload(cluster, "DaemonSet", item, core))
            for item in batch.list_job_for_all_namespaces().items:
                result.append(self._workload(cluster, "Job", item, core))
        except Exception as exc:
            raise RuntimeError(f"Could not list Kubernetes workloads: {exc}") from exc
        return result

    def metrics(self, cluster: Cluster, workload: Workload, time_range: str = "24h") -> list[MetricTimeSeriesPoint]:
        from app.storage.db import db
        creds = db.get_cluster_credentials(cluster.id)
        connection = self.verify(
            requested_endpoint=cluster.apiEndpoint,
            auth_method=creds.get("auth_method", "local"),
            kubeconfig_raw=creds.get("kubeconfig_raw"),
            bearer_token=creds.get("bearer_token")
        )
        settings_url = getattr(cluster, "prometheusUrl", None) or creds.get("prometheus_url") or os.getenv("PROMETHEUS_URL", "").strip()
        if not settings_url:
            settings_url = db.get_settings().prometheusUrl.strip()
        if not settings_url:
            settings_url = "http://localhost:9090"

        duration = re.fullmatch(r"([1-9][0-9]*)(m|h|d)", time_range)
        if not duration:
            raise ValueError("range must be a duration such as 1h, 24h, or 7d")
        count, unit = int(duration.group(1)), duration.group(2)
        seconds = count * {"m": 60, "h": 3600, "d": 86400}[unit]
        end = datetime.now(timezone.utc).timestamp()
        step = max(30, min(300, seconds // 240 or 30))
        namespace_match = json.dumps(workload.namespace)
        pod_match = json.dumps(f"^{re.escape(workload.name)}-.*")
        matcher = f'namespace={namespace_match},pod=~{pod_match},container!="",image!=""'
        queries = {
            "cpu": f"sum(rate(container_cpu_usage_seconds_total{{{matcher}}}[5m]))",
            "memory": f"sum(container_memory_working_set_bytes{{{matcher}}}) / 1024 / 1024",
        }
        series: dict[str, dict[float, float]] = {}
        for key, query in queries.items():
            params = urlencode({"query": query, "start": end - seconds, "end": end, "step": step})
            url = f"{settings_url.rstrip('/')}/api/v1/query_range?{params}"
            try:
                with urlopen(url, timeout=10) as response:
                    payload = json.load(response)
            except (HTTPError, URLError, TimeoutError) as exc:
                raise RuntimeError(f"Prometheus query failed: {exc}") from exc
            if payload.get("status") != "success":
                raise RuntimeError(f"Prometheus rejected the {key} query.")
            values: dict[float, float] = {}
            for item in payload.get("data", {}).get("result", []):
                for stamp, value in item.get("values", []):
                    try:
                        numeric = float(value)
                        if math.isfinite(numeric):
                            values[float(stamp)] = values.get(float(stamp), 0.0) + numeric
                    except (TypeError, ValueError):
                        continue
            series[key] = values

        points = []
        for stamp in sorted(set(series["cpu"]) & set(series["memory"])):
            points.append(MetricTimeSeriesPoint(
                timestamp=datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                cpuUsage=series["cpu"][stamp],
                cpuRequest=workload.cpuRequestCores * workload.replicasDesired,
                cpuLimit=workload.cpuLimitCores * workload.replicasDesired,
                memoryUsageMb=series["memory"][stamp],
                memoryLimitMb=workload.memoryLimitMb * workload.replicasDesired,
            ))
        if not points:
            raise RuntimeError("Prometheus returned no matching CPU and memory samples for this workload.")
        return points


cluster_collector = ClusterCollector()
