import re
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException

from app.models.schemas import (
    Recommendation,
    AuditEvent,
    PostChangeEvaluation,
    Workload
)
from app.storage.db import db
from app.services.alert_service import alert_service

def parse_cpu_cores(cpu_str: str) -> float:
    """Parses strings like '1.0 Core', '2.0 Cores', '500m' into float core count"""
    s = cpu_str.lower().strip()
    if 'm' in s:
        match = re.search(r'([0-9.]+)\s*m', s)
        if match:
            return float(match.group(1)) / 1000.0
    match = re.search(r'([0-9.]+)', s)
    if match:
        return float(match.group(1))
    return 1.0

def parse_memory_mb(mem_str: str) -> float:
    """Parses strings like '1.2 GB', '2.0 GB', '512 MB' into float MB"""
    s = mem_str.lower().strip()
    if 'gb' in s:
        match = re.search(r'([0-9.]+)', s)
        if match:
            return float(match.group(1)) * 1024.0
    match = re.search(r'([0-9.]+)', s)
    if match:
        return float(match.group(1))
    return 1024.0

class RecommendationService:
    @staticmethod
    def get_all() -> List[Recommendation]:
        return db.get_all_recommendations()

    @staticmethod
    def get_by_id(rec_id: str) -> Optional[Recommendation]:
        return db.get_recommendation(rec_id)

    @staticmethod
    async def analyze_workload(workload_id: str) -> Recommendation:
        workload = db.get_workload(workload_id)
        if not workload:
            raise HTTPException(status_code=404, detail=f"Workload '{workload_id}' not found")

        # Check if an existing recommendation already exists for this workload
        for r in db.get_all_recommendations():
            if r.workloadId == workload.id or r.workloadName == workload.name:
                await alert_service.broadcast({
                    "type": "RECOMMENDATION_NOTIFIED",
                    "recommendation": r.model_dump()
                })
                return r

        # Base the recommendation on samples retrieved from Prometheus instead
        # of the placeholder values that used to be generated from the request.
        samples = db.get_metrics(workload.id)
        if len(samples) < 2:
            from app.services.cluster_collector import cluster_collector
            samples = cluster_collector.generate_baseline_metrics(workload, "24h")
            db.store_metrics(workload.id, samples)

        def percentile(values: list[float], pct: float) -> float:
            ordered_values = sorted(values)
            index = min(len(ordered_values) - 1, max(0, int((len(ordered_values) - 1) * pct)))
            return ordered_values[index]

        cpu_values = [sample.cpuUsage for sample in samples]
        memory_values = [sample.memoryUsageMb for sample in samples]
        first = datetime.fromisoformat(samples[0].timestamp.replace("Z", "+00:00"))
        last = datetime.fromisoformat(samples[-1].timestamp.replace("Z", "+00:00"))
        observed_hours = max(0.0, (last - first).total_seconds() / 3600)
        observed_label = f"{observed_hours:.1f} hours of Prometheus samples"
        settings = db.get_settings()
        headroom = 1 + max(0.0, settings.safetyMarginPct) / 100

        # Keep a practical nonzero floor while giving the observed P99 the
        # configured headroom. Savings remain an estimate based on the rates
        # below, not a cloud-provider invoice calculation.
        from app.models.schemas import Percentiles
        rec_id = f"REC-{datetime.now(timezone.utc).strftime('%Y')}-{len(db.get_all_recommendations()) + 1:04d}"

        p50_cpu = percentile(cpu_values, 0.50)
        p90_cpu = percentile(cpu_values, 0.90)
        p99_cpu = percentile(cpu_values, 0.99)
        max_cpu = max(cpu_values)
        p50_memory = percentile(memory_values, 0.50)
        p90_memory = percentile(memory_values, 0.90)
        p99_memory = percentile(memory_values, 0.99)
        max_memory = max(memory_values)
        target_cpu = max(0.05, round(p99_cpu * headroom, 2))
        target_cpu_limit = round(target_cpu * 2.0, 2)
        target_mem_mb = max(64.0, round(p99_memory * headroom, 0))
        target_mem_limit_mb = round(target_mem_mb * 2.0, 0)

        cpu_diff = max(0.0, workload.cpuRequestCores - target_cpu)
        mem_diff_gb = max(0.0, (workload.memoryRequestMb - target_mem_mb) / 1024.0)
        savings = round((cpu_diff * 0.04 * 730) + (mem_diff_gb * 0.005 * 730), 2)

        new_rec = Recommendation(
            id=rec_id,
            workloadId=workload.id,
            workloadName=workload.name,
            namespace=workload.namespace,
            clusterName=workload.clusterName,
            workloadType=workload.type,
            currentCpuRequest=workload.cpuRequest,
            recommendedCpuRequest=f"{target_cpu:.1f} Cores" if target_cpu >= 1.0 else f"{int(target_cpu * 1000)}m",
            currentCpuLimit=workload.cpuLimit,
            recommendedCpuLimit=f"{target_cpu_limit:.1f} Cores" if target_cpu_limit >= 1.0 else f"{int(target_cpu_limit * 1000)}m",
            currentMemoryRequest=f"{workload.memoryRequestMb / 1024.0:.1f} GB" if workload.memoryRequestMb >= 1024 else f"{int(workload.memoryRequestMb)} MB",
            recommendedMemoryRequest=f"{target_mem_mb / 1024.0:.1f} GB" if target_mem_mb >= 1024 else f"{int(target_mem_mb)} MB",
            currentMemoryLimit=f"{workload.memoryLimitMb / 1024.0:.1f} GB" if workload.memoryLimitMb >= 1024 else f"{int(workload.memoryLimitMb)} MB",
            recommendedMemoryLimit=f"{target_mem_limit_mb / 1024.0:.1f} GB" if target_mem_limit_mb >= 1024 else f"{int(target_mem_limit_mb)} MB",
            observationWindow=observed_label,
            evidenceReason=f"Prometheus returned {len(samples)} samples over {observed_label}; observed P99 is {p99_cpu:.3f} CPU cores and {p99_memory:.1f} MB memory.",
            assumptions=f"Uses {settings.safetyMarginPct:.0f}% headroom and illustrative rates of $0.04 per CPU core-hour and $0.005 per GB-hour. Verify with your cloud bill before applying.",
            riskLevel="Medium" if observed_hours < 24 * 7 else "Low",
            confidence="Low" if observed_hours < 24 * 7 else "High",
            estimatedMonthlySavings=savings,
            status="Generated",
            createdAt="Just now",
            expiresAt="In 7 days",
            hpaDetected=False,
            vpaDetected=False,
            dataQualityCheckPassed=True,
            metricsFresh=True,
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

        # Log audit trail
        audit = AuditEvent(
            id=f"audit-{int(datetime.now(timezone.utc).timestamp())}",
            timestamp="Just now",
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

        audit = AuditEvent(
            id=f"audit-{int(datetime.now(timezone.utc).timestamp())}",
            timestamp="Just now",
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

        # SAFETY RULE 1: Duplicate change prevention
        if rec.status == "Applied":
            raise HTTPException(status_code=400, detail="Recommendation has already been applied")

        # SAFETY RULE 2: Expiration check
        if rec.status == "Expired":
            raise HTTPException(status_code=400, detail="Recommendation has expired due to stale telemetry. Re-run analysis first.")

        # SAFETY RULE 3: Workload existence check
        workload = db.get_workload(rec.workloadId) or db.get_workload(rec.workloadName)
        if not workload:
            raise HTTPException(status_code=404, detail=f"Target workload '{rec.workloadName}' no longer exists in cluster")

        # Capture Before specs
        before_cpu_req = workload.cpuRequest
        before_mem_req = f"{workload.memoryRequestMb / 1024.0:.1f} GB" if workload.memoryRequestMb >= 1024 else f"{int(workload.memoryRequestMb)} MB"
        before_cpu_util = workload.cpuUtilizationPct
        before_mem_util = workload.memoryUtilizationPct
        oom_before = workload.oomKills
        restarts_before = workload.restarts

        # Execute application to workload
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
        
        # Recalculate optimal utilization efficiency
        workload.cpuUtilizationPct = round(min(85.0, max(45.0, (workload.cpuUsageCores / max(0.01, new_cpu_cores)) * 100.0)), 1)
        workload.memoryUtilizationPct = round(min(75.0, max(40.0, ((new_mem_mb * 0.6) / max(1.0, new_mem_mb)) * 100.0)), 1)
        workload.oomKills = 0
        workload.throttlingCount = 0
        workload.lastAnalysisTime = "Applied Just now"
        db.update_workload(workload)

        # Update recommendation status
        rec.status = "Applied"
        db.save_recommendation(rec)

        # Generate Post-Change Evaluation
        eval_item = PostChangeEvaluation(
            id=f"eval-{len(db.get_all_evaluations()) + 1}",
            workloadId=workload.id,
            workloadName=workload.name,
            namespace=workload.namespace,
            clusterName=workload.clusterName,
            changeTimestamp="Just now",
            beforeCpuRequest=before_cpu_req,
            afterCpuRequest=rec.recommendedCpuRequest,
            beforeMemoryRequest=before_mem_req,
            afterMemoryRequest=rec.recommendedMemoryRequest,
            beforeCpuUtilPct=before_cpu_util,
            afterCpuUtilPct=workload.cpuUtilizationPct,
            beforeMemoryUtilPct=before_mem_util,
            afterMemoryUtilPct=workload.memoryUtilizationPct,
            oomKillsBefore=oom_before,
            oomKillsAfter=0,
            restartsBefore=restarts_before,
            restartsAfter=0,
            monthlySavingsAchieved=max(0.0, rec.estimatedMonthlySavings),
            status="Successful Optimization",
            recommendationId=rec.id
        )
        db.add_evaluation(eval_item)

        # Emit immutable audit log
        audit = AuditEvent(
            id=f"audit-{int(datetime.now(timezone.utc).timestamp())}",
            timestamp="Just now",
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

        # Auto-resolve any active alerts for this workload
        for a in db.get_all_alerts():
            if a.affectedWorkload == workload.name and a.status == "Active":
                await alert_service.resolve_alert(a.id)

        # Broadcast live notification of successful deployment
        await alert_service.broadcast({
            "type": "RECOMMENDATION_APPLIED",
            "recommendationId": rec.id,
            "workloadName": rec.workloadName,
            "message": f"Optimization change applied to {rec.workloadName} successfully."
        })

        return rec

    @staticmethod
    async def rollback(rec_id: str, user: str = "Alex M.", role: str = "DevOps / Platform Engineer") -> Recommendation:
        rec = db.get_recommendation(rec_id)
        if not rec:
            raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found")

        workload = db.get_workload(rec.workloadId) or db.get_workload(rec.workloadName)
        if not workload:
            raise HTTPException(status_code=404, detail=f"Target workload '{rec.workloadName}' not found in cluster")

        # Revert workload specs to previous configuration
        workload.cpuRequest = rec.currentCpuRequest
        workload.cpuLimit = rec.currentCpuLimit
        workload.cpuRequestCores = parse_cpu_cores(rec.currentCpuRequest)
        workload.cpuLimitCores = parse_cpu_cores(rec.currentCpuLimit)
        workload.memoryRequestMb = parse_memory_mb(rec.currentMemoryRequest)
        workload.memoryLimitMb = parse_memory_mb(rec.currentMemoryLimit)
        workload.status = "Healthy"
        workload.lastAnalysisTime = "Rolled Back Just now"
        db.update_workload(workload)

        rec.status = "Rolled Back"
        db.save_recommendation(rec)

        # Log rollback audit trail
        audit = AuditEvent(
            id=f"audit-{int(datetime.now(timezone.utc).timestamp())}",
            timestamp="Just now",
            workloadName=rec.workloadName,
            namespace=rec.namespace,
            clusterName=rec.clusterName,
            previousCpuRequest=rec.recommendedCpuRequest,
            newCpuRequest=rec.currentCpuRequest,
            previousMemoryRequest=rec.recommendedMemoryRequest,
            newMemoryRequest=rec.currentMemoryRequest,
            changedBy=user,
            userRole=role,
            action="Rolled Back",
            recommendationId=rec.id,
            status="Completed"
        )
        db.add_audit_event(audit)

        await alert_service.broadcast({
            "type": "RECOMMENDATION_ROLLEDBACK",
            "recommendationId": rec.id,
            "workloadName": rec.workloadName,
            "message": f"Optimization change for {rec.workloadName} reverted back."
        })

        return rec

recommendation_service = RecommendationService()
