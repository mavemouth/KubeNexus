import math
import re
from datetime import datetime, timezone
import uuid
from typing import List, Optional, Tuple, Any
from fastapi import HTTPException

from app.models.schemas import (
    Recommendation,
    AuditEvent,
    Workload,
    Percentiles,
    MetricTimeSeriesPoint
)
from app.storage.db import db
from app.services.alert_service import alert_service
from app.services.cluster_collector import cluster_collector


def parse_cpu_cores(cpu_val: Any) -> float:
    """Parses standard Kubernetes CPU resource values into float cores."""
    if cpu_val is None:
        return 0.1
    s = str(cpu_val).strip()
    if not s:
        return 0.1

    if s.endswith("n"):
        try:
            return float(s[:-1].strip()) / 1_000_000_000.0
        except ValueError:
            pass

    if s.endswith("u"):
        try:
            return float(s[:-1].strip()) / 1_000_000.0
        except ValueError:
            pass

    m_match = re.search(r"^([0-9.]+)\s*m$", s, re.IGNORECASE)
    if m_match:
        try:
            return float(m_match.group(1)) / 1000.0
        except ValueError:
            pass

    num_match = re.search(r"^([0-9.]+)(?:\s*cores?)?$", s, re.IGNORECASE)
    if num_match:
        try:
            return float(num_match.group(1))
        except ValueError:
            pass

    any_num = re.search(r"([0-9.]+)", s)
    if any_num:
        try:
            val = float(any_num.group(1))
            if "m" in s.lower():
                return val / 1000.0
            return val
        except ValueError:
            pass

    return 0.1


def parse_memory_mb(mem_val: Any) -> float:
    """Parses standard Kubernetes memory resource values into float Megabytes (MB)."""
    if mem_val is None:
        return 128.0
    s = str(mem_val).strip()
    if not s:
        return 128.0

    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]*)", s)
    if match:
        try:
            amount = float(match.group(1))
            unit = match.group(2)
            factors = {
                "Ki": 1.0 / 1024.0,
                "Mi": 1.0,
                "Gi": 1024.0,
                "Ti": 1024.0 ** 2,
                "Pi": 1024.0 ** 3,
                "Ei": 1024.0 ** 4,
                "KIB": 1.0 / 1024.0,
                "MIB": 1.0,
                "GIB": 1024.0,
                "TIB": 1024.0 ** 2,
                "KB": 1000.0 / 1024.0 / 1024.0,
                "MB": 1.0,
                "GB": 1024.0,
                "TB": 1024.0 ** 2,
                "K": 1000.0 / 1024.0 / 1024.0,
                "M": (1000.0 ** 2) / (1024.0 ** 2),
                "G": (1000.0 ** 3) / (1024.0 ** 2),
                "T": (1000.0 ** 4) / (1024.0 ** 2),
                "": 1.0 / (1024.0 ** 2)
            }
            factor = factors.get(unit, 1.0)
            return amount * factor
        except (ValueError, KeyError):
            pass

    any_num = re.search(r"([0-9.]+)", s)
    if any_num:
        try:
            val = float(any_num.group(1))
            if "gb" in s.lower() or "gi" in s.lower():
                return val * 1024.0
            return val
        except ValueError:
            pass

    return 128.0


def format_cpu_cores(cores: float) -> str:
    """Formats float cores into canonical Kubernetes CPU quantity string."""
    if cores < 1.0:
        return f"{max(1, int(round(cores * 1000)))}m"
    return f"{cores:.1f} Cores" if round(cores, 1) != round(cores, 2) else f"{cores:.2f} Cores"


def format_memory_mb(mb: float) -> str:
    """Formats float MB into canonical memory quantity string."""
    if mb >= 1024.0:
        gb = mb / 1024.0
        return f"{gb:.1f} GB"
    return f"{int(round(mb))} MB"


def calculate_percentile(sorted_values: List[float], pct: float) -> float:
    """Calculates percentile using standard linear interpolation."""
    if not sorted_values:
        raise ValueError("Cannot compute percentiles on an empty list")
    n = len(sorted_values)
    if n == 1:
        return float(sorted_values[0])
    index = pct * (n - 1)
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    fraction = index - lower
    if lower == upper:
        return float(sorted_values[lower])
    return float(sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower]))


class RecommendationService:
    @staticmethod
    def get_all() -> List[Recommendation]:
        return db.get_all_recommendations()

    @staticmethod
    def get_by_id(rec_id: str) -> Optional[Recommendation]:
        return db.get_recommendation(rec_id)

    @staticmethod
    def validate_metrics(
        samples: List[MetricTimeSeriesPoint],
        min_observation_days: int = 7,
        max_staleness_hours: float = 72.0
    ) -> Tuple[bool, str, float, List[float], List[float]]:
        if not samples or len(samples) < 2:
            return False, "Insufficient observations: at least 2 Prometheus telemetry samples are required.", 0.0, [], []

        valid_cpu = []
        valid_mem = []
        parsed_timestamps = []

        for idx, sample in enumerate(samples):
            if sample.cpuUsage is None or not math.isfinite(sample.cpuUsage) or sample.cpuUsage < 0.0:
                return False, f"Invalid or missing CPU usage metric detected at index {idx}.", 0.0, [], []
            if sample.memoryUsageMb is None or not math.isfinite(sample.memoryUsageMb) or sample.memoryUsageMb < 0.0:
                return False, f"Invalid or missing Memory usage metric detected at index {idx}.", 0.0, [], []

            valid_cpu.append(float(sample.cpuUsage))
            valid_mem.append(float(sample.memoryUsageMb))

            try:
                ts_str = sample.timestamp.replace("Z", "+00:00")
                parsed_timestamps.append(datetime.fromisoformat(ts_str))
            except Exception:
                return False, f"Invalid ISO timestamp format detected at sample index {idx}: {sample.timestamp}", 0.0, [], []

        sorted_timestamps = sorted(parsed_timestamps)
        first_ts = sorted_timestamps[0]
        last_ts = sorted_timestamps[-1]
        now = datetime.now(timezone.utc)

        staleness_hours = (now - last_ts).total_seconds() / 3600.0
        if staleness_hours > max_staleness_hours:
            return False, f"Metric telemetry is stale: last sample observed {staleness_hours:.1f}h ago (threshold: {max_staleness_hours:.0f}h).", 0.0, [], []

        observed_hours = max(0.0, (last_ts - first_ts).total_seconds() / 3600.0)
        min_hours = min_observation_days * 24.0

        if observed_hours < min_hours:
            return False, f"Observation window of {observed_hours:.1f} hours is below the required minimum of {min_hours:.0f} hours ({min_observation_days} days).", observed_hours, valid_cpu, valid_mem

        return True, "Metric validation passed.", observed_hours, valid_cpu, valid_mem

    @staticmethod
    def classify_provisioning(
        current_cpu_request: float,
        target_cpu_request: float,
        current_mem_request: float,
        target_mem_request: float,
        oom_kills: int = 0,
        throttling_count: int = 0
    ) -> str:
        if oom_kills > 0 or throttling_count > 50:
            return "UNDERPROVISIONED"

        cpu_ratio = target_cpu_request / max(0.01, current_cpu_request)
        mem_ratio = target_mem_request / max(1.0, current_mem_request)

        if cpu_ratio > 1.10 or mem_ratio > 1.10:
            return "UNDERPROVISIONED"
        if cpu_ratio < 0.85 and mem_ratio < 0.85:
            return "OVERPROVISIONED"
        return "APPROPRIATELY_PROVISIONED"

    # -----------------------------------------------------------------------
    # Phase 2: Autoscaler Detection Methods (HPA & VPA)
    # -----------------------------------------------------------------------

    @classmethod
    def detect_hpa(cls, cluster: Any, namespace: str, workload_name: str, workload_type: str, client_override: Any = None) -> Dict[str, Any]:
        """Detects Horizontal Pod Autoscaler controlling the given workload."""
        try:
            autoscaling_api = client_override
            if not autoscaling_api:
                if not cluster:
                    return {"status": "UNAVAILABLE", "reason": "No cluster specified for HPA lookup."}
                creds = db.get_cluster_credentials(cluster.id)
                connection = cluster_collector.verify(
                    requested_endpoint=cluster.apiEndpoint,
                    auth_method=creds.get("auth_method", "local"),
                    kubeconfig_raw=creds.get("kubeconfig_raw"),
                    bearer_token=creds.get("bearer_token")
                )
                autoscaling_api = connection.get("autoscaling")

            if not autoscaling_api:
                return {"status": "UNAVAILABLE", "reason": "Autoscaling API client is not configured or available."}

            try:
                if hasattr(autoscaling_api, "list_namespaced_horizontal_pod_autoscaler"):
                    hpa_list = autoscaling_api.list_namespaced_horizontal_pod_autoscaler(namespace=namespace)
                else:
                    return {"status": "UNAVAILABLE", "reason": "HorizontalPodAutoscaler API method not found."}
            except Exception as e:
                return {"status": "UNAVAILABLE", "reason": f"Failed to query HPA resources from Kubernetes API: {e}"}

            for hpa in getattr(hpa_list, "items", []):
                spec = getattr(hpa, "spec", None)
                if not spec:
                    continue
                scale_target = getattr(spec, "scale_target_ref", None)
                if not scale_target:
                    continue

                target_name = getattr(scale_target, "name", None)
                target_kind = getattr(scale_target, "kind", None)

                if target_name == workload_name and (not target_kind or target_kind.lower() == workload_type.lower()):
                    status = getattr(hpa, "status", None)
                    metadata = getattr(hpa, "metadata", None)
                    hpa_name = getattr(metadata, "name", "unknown") if metadata else "unknown"

                    min_reps = getattr(spec, "min_replicas", 1)
                    max_reps = getattr(spec, "max_replicas", 1)
                    curr_reps = getattr(status, "current_replicas", None) if status else None
                    des_reps = getattr(status, "desired_replicas", None) if status else None

                    cpu_target = None
                    mem_target = None

                    metrics = getattr(spec, "metrics", []) or []
                    for m in metrics:
                        m_type = getattr(m, "type", "")
                        if m_type == "Resource":
                            res = getattr(m, "resource", None)
                            if res:
                                res_name = getattr(res, "name", "")
                                target_spec = getattr(res, "target", None)
                                avg_util = getattr(target_spec, "average_utilization", None) if target_spec else None
                                if res_name == "cpu":
                                    cpu_target = avg_util
                                elif res_name == "memory":
                                    mem_target = avg_util

                    if cpu_target is None and hasattr(spec, "target_cpu_utilization_percentage"):
                        cpu_target = getattr(spec, "target_cpu_utilization_percentage", None)

                    conditions = []
                    if status and hasattr(status, "conditions") and status.conditions:
                        for cond in status.conditions:
                            c_type = getattr(cond, "type", "")
                            c_status = getattr(cond, "status", "")
                            conditions.append(f"{c_type}={c_status}")

                    return {
                        "status": "DETECTED",
                        "hpaName": hpa_name,
                        "targetWorkload": target_name,
                        "minReplicas": min_reps,
                        "maxReplicas": max_reps,
                        "currentReplicas": curr_reps,
                        "desiredReplicas": des_reps,
                        "cpuTargetPercent": cpu_target,
                        "memoryTargetPercent": mem_target,
                        "conditions": conditions
                    }

            return {"status": "NOT_DETECTED"}

        except Exception as exc:
            return {"status": "UNAVAILABLE", "reason": str(exc)}

    @classmethod
    def detect_vpa(cls, cluster: Any, namespace: str, workload_name: str, workload_type: str, client_override: Any = None) -> Dict[str, Any]:
        """Detects Vertical Pod Autoscaler controlling the given workload."""
        try:
            custom_api = client_override
            if not custom_api:
                if not cluster:
                    return {"status": "UNAVAILABLE", "reason": "No cluster specified for VPA lookup."}
                creds = db.get_cluster_credentials(cluster.id)
                connection = cluster_collector.verify(
                    requested_endpoint=cluster.apiEndpoint,
                    auth_method=creds.get("auth_method", "local"),
                    kubeconfig_raw=creds.get("kubeconfig_raw"),
                    bearer_token=creds.get("bearer_token")
                )
                custom_api = connection.get("custom_objects")

            if not custom_api:
                return {"status": "UNAVAILABLE", "reason": "CustomObjectsApi client is not configured or available."}

            try:
                vpa_list = custom_api.list_namespaced_custom_object(
                    group="autoscaling.k8s.io",
                    version="v1",
                    namespace=namespace,
                    plural="verticalpodautoscalers"
                )
            except Exception as e:
                return {"status": "UNAVAILABLE", "reason": f"VerticalPodAutoscaler CRD is unavailable or not queryable: {e}"}

            items = vpa_list.get("items", []) if isinstance(vpa_list, dict) else []
            for item in items:
                spec = item.get("spec", {})
                target_ref = spec.get("targetRef", {})
                target_name = target_ref.get("name")
                target_kind = target_ref.get("kind", "")

                if target_name == workload_name and (not target_kind or target_kind.lower() == workload_type.lower()):
                    metadata = item.get("metadata", {})
                    vpa_name = metadata.get("name", "unknown")
                    update_policy = spec.get("updatePolicy", {})
                    update_mode = update_policy.get("updateMode", "Auto")
                    resource_policy = spec.get("resourcePolicy", {})

                    vpa_status = item.get("status", {})
                    recommendation_data = vpa_status.get("recommendation", {})
                    container_recs = recommendation_data.get("containerRecommendations", [])

                    cpu_rec = None
                    mem_rec = None
                    if container_recs:
                        target_specs = container_recs[0].get("target", {})
                        cpu_rec = target_specs.get("cpu")
                        mem_rec = target_specs.get("memory")

                    return {
                        "status": "DETECTED",
                        "vpaName": vpa_name,
                        "targetWorkload": target_name,
                        "updateMode": update_mode,
                        "resourcePolicy": resource_policy,
                        "containerRecommendations": container_recs,
                        "cpuRecommendation": cpu_rec,
                        "memoryRecommendation": mem_rec,
                        "statusDetails": vpa_status
                    }

            return {"status": "NOT_DETECTED"}

        except Exception as exc:
            return {"status": "UNAVAILABLE", "reason": str(exc)}

    @classmethod
    def evaluate_safety_rules(cls, hpa_info: Dict[str, Any], vpa_info: Dict[str, Any]) -> Tuple[str, List[str], List[str], bool]:
        """Evaluates autoscaler detection findings against safety rules."""
        safety_status = "SAFE"
        warnings: List[str] = []
        blocked_reasons: List[str] = []
        requires_review = False

        if hpa_info.get("status") == "UNAVAILABLE" or vpa_info.get("status") == "UNAVAILABLE":
            safety_status = "UNKNOWN"
            unavailable_reasons = []
            if hpa_info.get("status") == "UNAVAILABLE":
                unavailable_reasons.append(f"HPA check unavailable ({hpa_info.get('reason', 'API error')})")
            if vpa_info.get("status") == "UNAVAILABLE":
                unavailable_reasons.append(f"VPA check unavailable ({vpa_info.get('reason', 'API error')})")
            warning_msg = f"Autoscaler status could not be verified: {'; '.join(unavailable_reasons)}. Manual inspection recommended before applying changes."
            warnings.append(warning_msg)
            requires_review = True

        if vpa_info.get("status") == "DETECTED":
            update_mode = vpa_info.get("updateMode", "Auto")
            vpa_name = vpa_info.get("vpaName", "VPA")
            if update_mode.lower() in ["auto", "recreate", "initial"]:
                safety_status = "BLOCKED"
                blocked_reasons.append(
                    f"Workload is controlled by active VPA '{vpa_name}' with updateMode='{update_mode}'. "
                    f"Manual resource request changes conflict with VPA actuation and will be overwritten or cause flapping."
                )
                requires_review = True
            elif update_mode.lower() == "off":
                if safety_status != "BLOCKED":
                    safety_status = "WARNING"
                warnings.append(
                    f"Workload is tracked by VPA '{vpa_name}' in 'Off' (recommendation-only) mode. Verify recommendations align with VPA guidance."
                )

        if hpa_info.get("status") == "DETECTED":
            hpa_name = hpa_info.get("hpaName", "HPA")
            cpu_target = hpa_info.get("cpuTargetPercent")
            mem_target = hpa_info.get("memoryTargetPercent")

            if cpu_target is not None:
                if safety_status != "BLOCKED":
                    safety_status = "WARNING"
                warnings.append(
                    f"HPA '{hpa_name}' scales pods using target CPU utilization of {cpu_target}%. "
                    f"Adjusting CPU requests alters the baseline denominator and directly changes autoscaling sensitivity!"
                )
                requires_review = True

            if mem_target is not None:
                if safety_status != "BLOCKED":
                    safety_status = "WARNING"
                warnings.append(
                    f"HPA '{hpa_name}' scales pods using target Memory utilization of {mem_target}%. "
                    f"Adjusting Memory requests alters the baseline denominator and directly affects horizontal pod scaling!"
                )
                requires_review = True

            if cpu_target is None and mem_target is None:
                if safety_status != "BLOCKED":
                    safety_status = "WARNING"
                warnings.append(
                    f"Workload is controlled by HPA '{hpa_name}' (min: {hpa_info.get('minReplicas')}, max: {hpa_info.get('maxReplicas')}). Changing pod specs may trigger replica rebalancing."
                )

        return safety_status, warnings, blocked_reasons, requires_review

    @classmethod
    async def analyze_workload(cls, workload_id: str, force_reanalyze: bool = False) -> Recommendation:
        workload = db.get_workload(workload_id)
        if not workload:
            raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")

        if not force_reanalyze:
            for r in db.get_all_recommendations():
                if (r.workloadId == workload.id or r.workloadName == workload.name) and r.status in ["Generated", "Reviewed"]:
                    await alert_service.broadcast({
                        "type": "RECOMMENDATION_NOTIFIED",
                        "recommendation": r.model_dump()
                    })
                    return r

        samples = db.get_metrics(workload.id)
        settings = db.get_settings()
        min_days = getattr(settings, "minObservationDays", 7)

        is_valid, validation_msg, observed_hours, cpu_values, memory_values = cls.validate_metrics(
            samples, min_observation_days=min_days
        )

        if len(samples) < 2:
            raise HTTPException(
                status_code=409,
                detail=f"At least two Prometheus samples are required before analysis. Classification: INSUFFICIENT_DATA. {validation_msg}"
            )

        ordered_cpu = sorted(cpu_values)
        ordered_memory = sorted(memory_values)

        p50_cpu = calculate_percentile(ordered_cpu, 0.50)
        p90_cpu = calculate_percentile(ordered_cpu, 0.90)
        p99_cpu = calculate_percentile(ordered_cpu, 0.99)
        max_cpu = max(ordered_cpu)

        p50_memory = calculate_percentile(ordered_memory, 0.50)
        p90_memory = calculate_percentile(ordered_memory, 0.90)
        p99_memory = calculate_percentile(ordered_memory, 0.99)
        max_memory = max(ordered_memory)

        observed_days = observed_hours / 24.0
        observed_label = (
            f"{observed_days:.1f}-day continuous analysis"
            if observed_days >= 1.0
            else f"{observed_hours:.1f}-hour observation window"
        )

        headroom_pct = max(0.0, float(settings.safetyMarginPct))
        headroom = 1.0 + (headroom_pct / 100.0)

        target_cpu = max(0.05, round(p99_cpu * headroom, 3))
        target_cpu_limit = round(target_cpu * 2.0, 3)
        target_mem_mb = max(64.0, round(p99_memory * headroom, 1))
        target_mem_limit_mb = round(target_mem_mb * 2.0, 1)

        curr_cpu_req = max(0.01, workload.cpuRequestCores)
        curr_mem_req = max(1.0, workload.memoryRequestMb)

        classification = cls.classify_provisioning(
            current_cpu_request=curr_cpu_req,
            target_cpu_request=target_cpu,
            current_mem_request=curr_mem_req,
            target_mem_request=target_mem_mb,
            oom_kills=workload.oomKills,
            throttling_count=workload.throttlingCount
        )

        cpu_diff = curr_cpu_req - target_cpu
        mem_diff_gb = (curr_mem_req - target_mem_mb) / 1024.0
        monthly_cost_impact = round((cpu_diff * 0.04 * 730) + (mem_diff_gb * 0.005 * 730), 2)

        if not is_valid:
            confidence = "Low"
            risk_level = "High"
            risk_description = f"High risk: telemetry does not meet recommended {min_days}-day observation baseline ({validation_msg})."
        elif classification == "UNDERPROVISIONED":
            confidence = "High"
            risk_level = "Low"
            risk_description = "Low operational risk: scaling up resources alleviates container throttling and OOMKill failure risks."
        elif classification == "OVERPROVISIONED":
            confidence = "High" if observed_days >= min_days else "Medium"
            risk_level = "Low" if observed_days >= 14 else "Medium"
            risk_description = "Medium risk of resource pressure during unobserved traffic peaks; protected by safety margin headroom."
        else:
            confidence = "High" if observed_days >= min_days else "Medium"
            risk_level = "Low"
            risk_description = "Low risk: workload is currently operating near optimal resource utilization bounds."

        evidence_reason = (
            f"Classification: {classification}. Evaluated {len(samples)} valid Prometheus telemetry samples over {observed_label}. "
            f"Observed CPU: P50={p50_cpu:.3f}, P90={p90_cpu:.3f}, P99={p99_cpu:.3f} cores (Peak={max_cpu:.3f}). "
            f"Observed Memory: P50={p50_memory:.1f} MB, P90={p90_memory:.1f} MB, P99={p99_memory:.1f} MB (Peak={max_memory:.1f} MB). "
            f"{risk_description}"
        )

        # -------------------------------------------------------------------
        # Phase 2: Live Kubernetes Autoscaler Detection & Safety Rules
        # -------------------------------------------------------------------
        cluster = db.get_cluster(workload.clusterId)
        hpa_info = {"status": "UNAVAILABLE", "reason": "Cluster configuration not found"}
        vpa_info = {"status": "UNAVAILABLE", "reason": "Cluster configuration not found"}

        if cluster:
            hpa_info = cls.detect_hpa(cluster, workload.namespace, workload.name, workload.type)
            vpa_info = cls.detect_vpa(cluster, workload.namespace, workload.name, workload.type)

        safety_status, safety_warnings, blocked_reasons, requires_manual_review = cls.evaluate_safety_rules(
            hpa_info=hpa_info,
            vpa_info=vpa_info
        )

        hpa_detected = (hpa_info.get("status") == "DETECTED")
        vpa_detected = (vpa_info.get("status") == "DETECTED")

        autoscaler_status_parts = []
        if hpa_detected:
            autoscaler_status_parts.append(f"HPA:{hpa_info.get('hpaName')}")
        if vpa_detected:
            autoscaler_status_parts.append(f"VPA:{vpa_info.get('vpaName')}({vpa_info.get('updateMode')})")
        if not autoscaler_status_parts:
            if hpa_info.get("status") == "NOT_DETECTED" and vpa_info.get("status") == "NOT_DETECTED":
                autoscaler_status_str = "NONE_DETECTED"
            else:
                autoscaler_status_str = "UNVERIFIED"
        else:
            autoscaler_status_str = ", ".join(autoscaler_status_parts)

        # Confidence & Risk modulation based on Safety Status
        if safety_status == "BLOCKED":
            confidence = "Low"
            risk_level = "High"
            risk_description = f"Action Blocked: {blocked_reasons[0] if blocked_reasons else 'VPA conflict'}"
        elif not is_valid:
            confidence = "Low"
            risk_level = "High"
            risk_description = f"High risk: telemetry does not meet recommended {min_days}-day observation baseline ({validation_msg})."
        elif classification == "UNDERPROVISIONED":
            confidence = "High"
            risk_level = "Low"
            risk_description = "Low operational risk: scaling up resources alleviates container throttling and OOMKill failure risks."
        elif classification == "OVERPROVISIONED":
            confidence = "High" if observed_days >= min_days else "Medium"
            risk_level = "Low" if observed_days >= 14 else "Medium"
            risk_description = "Medium risk of resource pressure during unobserved traffic peaks; protected by safety margin headroom."
        else:
            confidence = "High" if observed_days >= min_days else "Medium"
            risk_level = "Low"
            risk_description = "Low risk: workload is currently operating near optimal resource utilization bounds."

        evidence_reason = (
            f"Classification: {classification}. Safety Status: {safety_status}. "
            f"Evaluated {len(samples)} valid Prometheus telemetry samples over {observed_label}. "
            f"Observed CPU: P50={p50_cpu:.3f}, P90={p90_cpu:.3f}, P99={p99_cpu:.3f} cores (Peak={max_cpu:.3f}). "
            f"Observed Memory: P50={p50_memory:.1f} MB, P90={p90_memory:.1f} MB, P99={p99_memory:.1f} MB (Peak={max_memory:.1f} MB). "
            f"{risk_description}"
        )

        warning_notes = (' Warnings: ' + ' '.join(safety_warnings)) if safety_warnings else ''
        blocked_notes = (' BLOCKED: ' + ' '.join(blocked_reasons)) if blocked_reasons else ''
        assumptions = (
            f"Engine configured with {headroom_pct:.0f}% safety headroom above P99 peak. "
            f"Illustrative cloud rates: $0.04/CPU core-hour, $0.005/GB-hour. "
            f"Autoscaler configuration: {autoscaler_status_str}.{warning_notes}{blocked_notes}"
        )

        now_utc = datetime.now(timezone.utc)
        rec_id = f"REC-{now_utc.strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"

        new_rec = Recommendation(
            id=rec_id,
            workloadId=workload.id,
            workloadName=workload.name,
            namespace=workload.namespace,
            clusterName=workload.clusterName,
            workloadType=workload.type,
            currentCpuRequest=workload.cpuRequest,
            recommendedCpuRequest=format_cpu_cores(target_cpu),
            currentCpuLimit=workload.cpuLimit,
            recommendedCpuLimit=format_cpu_cores(target_cpu_limit),
            currentMemoryRequest=format_memory_mb(workload.memoryRequestMb),
            recommendedMemoryRequest=format_memory_mb(target_mem_mb),
            currentMemoryLimit=format_memory_mb(workload.memoryLimitMb),
            recommendedMemoryLimit=format_memory_mb(target_mem_limit_mb),
            observationWindow=observed_label,
            evidenceReason=evidence_reason,
            assumptions=assumptions,
            riskLevel=risk_level,
            confidence=confidence,
            estimatedMonthlySavings=monthly_cost_impact,
            status="Generated",
            createdAt=now_utc.isoformat(),
            expiresAt="In 7 days",
            hpaDetected=hpa_detected,
            vpaDetected=vpa_detected,
            dataQualityCheckPassed=is_valid,
            metricsFresh=is_valid,
            autoscalerStatus=autoscaler_status_str,
            safetyStatus=safety_status,
            safetyWarnings=safety_warnings,
            blockedReasons=blocked_reasons,
            requiresManualReview=requires_manual_review,
            percentiles=Percentiles(
                p50Cpu=round(p50_cpu, 3),
                p90Cpu=round(p90_cpu, 3),
                p99Cpu=round(p99_cpu, 3),
                maxCpu=round(max_cpu, 3),
                p50MemoryMb=round(p50_memory, 1),
                p90MemoryMb=round(p90_memory, 1),
                p99MemoryMb=round(p99_memory, 1),
                maxMemoryMb=round(max_memory, 1)
            )
        )

        db.save_recommendation(new_rec)
        await alert_service.broadcast({
            "type": "RECOMMENDATION_NOTIFIED",
            "recommendation": new_rec.model_dump()
        })
        return new_rec

    @staticmethod
    async def approve(rec_id: str, user: str = "Alex M.", role: str = "DevOps / Platform Engineer") -> Recommendation:
        rec = db.get_recommendation(rec_id)
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found")

        if rec.status == "Applied":
            raise HTTPException(status_code=400, detail="Recommendation has already been applied")

        rec.status = "Approved"
        db.save_recommendation(rec)

        now_utc = datetime.now(timezone.utc)
        audit = AuditEvent(
            id=f"audit-{int(now_utc.timestamp())}-{uuid.uuid4().hex[:4]}",
            timestamp=now_utc.isoformat(),
            workloadName=rec.workloadName,
            namespace=rec.namespace,
            clusterName=rec.clusterName,
            previousCpuRequest=rec.currentCpuRequest,
            newCpuRequest=rec.recommendedCpuRequest,
            previousMemoryRequest=rec.currentMemoryRequest,
            newMemoryRequest=rec.recommendedMemoryRequest,
            changedBy=user,
            userRole=role,
            action="Approved",
            recommendationId=rec.id,
            status="Completed"
        )
        db.add_audit_event(audit)

        await alert_service.broadcast({
            "type": "RECOMMENDATION_APPROVED",
            "recommendationId": rec.id,
            "workloadName": rec.workloadName
        })

        return rec

    @staticmethod
    async def reject(rec_id: str, user: str = "Alex M.", role: str = "DevOps / Platform Engineer") -> Recommendation:
        rec = db.get_recommendation(rec_id)
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found")

        if rec.status == "Applied":
            raise HTTPException(status_code=400, detail="Cannot reject a recommendation that has already been applied")

        rec.status = "Rejected"
        db.save_recommendation(rec)

        now_utc = datetime.now(timezone.utc)
        audit = AuditEvent(
            id=f"audit-{int(now_utc.timestamp())}-{uuid.uuid4().hex[:4]}",
            timestamp=now_utc.isoformat(),
            workloadName=rec.workloadName,
            namespace=rec.namespace,
            clusterName=rec.clusterName,
            previousCpuRequest=rec.currentCpuRequest,
            newCpuRequest=rec.currentCpuRequest,
            previousMemoryRequest=rec.currentMemoryRequest,
            newMemoryRequest=rec.currentMemoryRequest,
            changedBy=user,
            userRole=role,
            action="Rejected",
            recommendationId=rec.id,
            status="Completed"
        )
        db.add_audit_event(audit)

        await alert_service.broadcast({
            "type": "RECOMMENDATION_REJECTED",
            "recommendationId": rec.id,
            "workloadName": rec.workloadName
        })

        return rec

    @staticmethod
    async def apply(rec_id: str, user: str = "Alex M.", role: str = "DevOps / Platform Engineer") -> Recommendation:
        rec = db.get_recommendation(rec_id)
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found")

        if rec.status == "Applied":
            raise HTTPException(status_code=400, detail="Recommendation has already been applied")

        if rec.status == "Expired":
            raise HTTPException(status_code=400, detail="Recommendation has expired due to stale telemetry. Re-run analysis first.")

        # Phase 2 Safety Rule Enforcement: Cannot apply BLOCKED recommendations
        if getattr(rec, "safetyStatus", "SAFE") == "BLOCKED":
            reasons = getattr(rec, "blockedReasons", ["Autoscaler conflict"])
            raise HTTPException(
                status_code=409,
                detail=f"Recommendation application is BLOCKED by autoscaler safety rules: {'; '.join(reasons)}"
            )

        workload = db.get_workload(rec.workloadId) or db.get_workload(rec.workloadName)
        if not workload:
            raise HTTPException(status_code=404, detail=f"Target workload '{rec.workloadName}' no longer exists in database")

        before_cpu_req = workload.cpuRequest
        before_mem_req = format_memory_mb(workload.memoryRequestMb)

        new_cpu_cores = parse_cpu_cores(rec.recommendedCpuRequest)
        new_mem_mb = parse_memory_mb(rec.recommendedMemoryRequest)
        new_cpu_limit_cores = parse_cpu_cores(rec.recommendedCpuLimit)
        new_mem_limit_mb = parse_memory_mb(rec.recommendedMemoryLimit)

        workload.cpuRequest = rec.recommendedCpuRequest
        workload.cpuLimit = rec.recommendedCpuLimit
        workload.cpuRequestCores = new_cpu_cores
        workload.cpuLimitCores = new_cpu_limit_cores
        workload.memoryRequestMb = new_mem_mb
        workload.memoryLimitMb = new_mem_limit_mb
        workload.status = "Healthy"
        now_utc = datetime.now(timezone.utc)
        workload.lastAnalysisTime = f"Applied target spec at {now_utc.isoformat()}"
        db.update_workload(workload)

        rec.status = "Applied"
        db.save_recommendation(rec)

        audit = AuditEvent(
            id=f"audit-{int(now_utc.timestamp())}-{uuid.uuid4().hex[:4]}",
            timestamp=now_utc.isoformat(),
            workloadName=rec.workloadName,
            namespace=rec.namespace,
            clusterName=rec.clusterName,
            previousCpuRequest=before_cpu_req,
            newCpuRequest=rec.recommendedCpuRequest,
            previousMemoryRequest=before_mem_req,
            newMemoryRequest=rec.recommendedMemoryRequest,
            changedBy=user,
            userRole=role,
            action="Applied",
            recommendationId=rec.id,
            status="Completed"
        )
        db.add_audit_event(audit)

        for a in db.get_all_alerts():
            if a.affectedWorkload == workload.name and a.status == "Active":
                await alert_service.resolve_alert(a.id)

        await alert_service.broadcast({
            "type": "RECOMMENDATION_APPLIED",
            "recommendationId": rec.id,
            "workloadName": rec.workloadName,
            "message": f"Optimization change recorded for {rec.workloadName}."
        })

        return rec


recommendation_service = RecommendationService()
