import asyncio
import json
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional

from app.models.schemas import AlertItem
from app.services.alert_service import alert_service

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])

@router.get("", response_model=List[AlertItem])
def get_alerts(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    return alert_service.get_alerts(severity=severity, status=status)

@router.get("/stream")
async def stream_notifications(request: Request):
    """
    Server-Sent Events (SSE) live notification stream.
    Pushes real-time alerts and optimization events to the frontend.
    """
    queue = alert_service.subscribe()

    async def event_generator():
        try:
            # Send initial connected event
            yield f"data: {json.dumps({'type': 'CONNECTED', 'message': 'Subscribed to KubeNexus live alert stream'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping
                    yield f": heartbeat\n\n"
        finally:
            alert_service.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.get("/{alert_id}", response_model=AlertItem)
def get_alert(alert_id: str):
    alert = alert_service.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert

@router.post("/{alert_id}/resolve", response_model=AlertItem)
async def resolve_alert(alert_id: str):
    alert = await alert_service.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert

@router.post("/{alert_id}/acknowledge", response_model=AlertItem)
async def acknowledge_alert(alert_id: str):
    alert = await alert_service.acknowledge_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert

@router.post("/scan")
async def trigger_rule_scan():
    """Runs automated health rules across all clusters and workloads"""
    await alert_service.scan_and_evaluate_rules()
    return {"status": "success", "message": "Automated alert rules evaluated across all clusters"}
