import asyncio
from typing import List, Optional, Set
from datetime import datetime, timezone

from app.models.schemas import AlertItem, AlertSeverity, Workload
from app.storage.db import db

class AlertService:
    def __init__(self):
        self._subscribers: Set[asyncio.Queue] = set()

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers.discard(q)

    async def broadcast(self, message: dict):
        """Broadcast live notification to all connected SSE / WebSocket listeners"""
        dead_queues = set()
        for q in self._subscribers:
            try:
                q.put_nowait(message)
            except Exception:
                dead_queues.add(q)
        self._subscribers.difference_update(dead_queues)

    def get_alerts(self, severity: Optional[str] = None, status: Optional[str] = None) -> List[AlertItem]:
        alerts = db.get_all_alerts()
        if severity and severity != 'all':
            alerts = [a for a in alerts if a.severity.lower() == severity.lower()]
        if status and status != 'all':
            alerts = [a for a in alerts if a.status.lower() == status.lower()]
        return alerts

    def get_alert_by_id(self, alert_id: str) -> Optional[AlertItem]:
        return db.get_alert(alert_id)

    async def resolve_alert(self, alert_id: str) -> Optional[AlertItem]:
        alert = db.get_alert(alert_id)
        if not alert:
            return None
        alert.status = "Resolved"
        db.save_alert(alert)
        await self.broadcast({
            "type": "ALERT_RESOLVED",
            "alertId": alert_id,
            "title": alert.title
        })
        return alert

    async def acknowledge_alert(self, alert_id: str) -> Optional[AlertItem]:
        alert = db.get_alert(alert_id)
        if not alert:
            return None
        alert.status = "Acknowledged"
        db.save_alert(alert)
        await self.broadcast({
            "type": "ALERT_ACKNOWLEDGED",
            "alertId": alert_id,
            "title": alert.title
        })
        return alert

    async def create_alert(
        self,
        severity: AlertSeverity,
        title: str,
        description: str,
        affected_workload: str,
        cluster_name: str,
        category: str = "Utilization"
    ) -> AlertItem:
        alert_id = f"alert-{len(db.get_all_alerts()) + 1}"
        new_alert = AlertItem(
            id=alert_id,
            severity=severity,
            title=title,
            description=description,
            affectedWorkload=affected_workload,
            clusterName=cluster_name,
            timestamp="Just now",
            status="Active",
            category=category # type: ignore
        )
        db.save_alert(new_alert)
        await self.broadcast({
            "type": "NEW_ALERT",
            "alert": new_alert.model_dump()
        })
        return new_alert

    async def scan_and_evaluate_rules(self):
        """Automated rule evaluation across all workloads and clusters"""
        workloads = db.get_all_workloads()
        for w in workloads:
            # Rule 1: Under-provisioning / OOMKill instability
            if w.oomKills > 0 or w.throttlingCount > 100 or w.cpuUtilizationPct > 90.0:
                existing = [a for a in db.get_all_alerts() if a.affectedWorkload == w.name and a.status == "Active" and a.category == "Provisioning"]
                if not existing:
                    await self.create_alert(
                        severity="Critical",
                        title=f"Critical Resource Saturation: {w.name}",
                        description=f"Workload {w.name} in {w.namespace} is experiencing extreme resource pressure ({w.cpuUtilizationPct:.1f}% CPU, {w.oomKills} OOMKills, {w.throttlingCount} throttles).",
                        affected_workload=w.name,
                        cluster_name=w.clusterName,
                        category="Provisioning"
                    )

            # Rule 2: Stale telemetry data
            if w.dataQualityStatus == "stale_data":
                existing = [a for a in db.get_all_alerts() if a.affectedWorkload == w.name and a.status == "Active" and a.category == "Data Quality"]
                if not existing:
                    await self.create_alert(
                        severity="Warning",
                        title=f"Telemetry Stream Interrupted: {w.name}",
                        description=f"Metrics collection agent has not received telemetry for {w.name} in over 48 hours. Optimizations paused.",
                        affected_workload=w.name,
                        cluster_name=w.clusterName,
                        category="Data Quality"
                    )

# Global singleton
alert_service = AlertService()
