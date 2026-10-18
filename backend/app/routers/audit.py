from fastapi import APIRouter
from typing import List

from app.models.schemas import AuditEvent
from app.storage.db import db

router = APIRouter(prefix="/audit-events", tags=["Audit Log"])

@router.get("", response_model=List[AuditEvent])
def get_audit_events():
    return db.get_all_audit_events()
