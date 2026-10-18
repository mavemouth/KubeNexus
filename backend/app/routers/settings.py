from fastapi import APIRouter
from app.models.schemas import OptimizationSettings
from app.storage.db import db
from app.services.alert_service import alert_service

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=OptimizationSettings)
def get_settings():
    return db.get_settings()

@router.post("", response_model=OptimizationSettings)
async def update_settings_post(new_settings: OptimizationSettings):
    updated = db.update_settings(new_settings)
    await alert_service.broadcast({
        "type": "SETTINGS_UPDATED",
        "settings": updated.model_dump()
    })
    return updated

@router.put("", response_model=OptimizationSettings)
async def update_settings_put(new_settings: OptimizationSettings):
    updated = db.update_settings(new_settings)
    await alert_service.broadcast({
        "type": "SETTINGS_UPDATED",
        "settings": updated.model_dump()
    })
    return updated
