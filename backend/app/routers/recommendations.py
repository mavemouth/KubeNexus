from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.models.schemas import Recommendation
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=List[Recommendation])
def get_recommendations():
    return recommendation_service.get_all()

@router.get("/{rec_id}", response_model=Recommendation)
def get_recommendation(rec_id: str):
    rec = recommendation_service.get_by_id(rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation '{rec_id}' not found")
    return rec

@router.post("/{rec_id}/approve", response_model=Recommendation)
async def approve_recommendation(rec_id: str):
    return await recommendation_service.approve(rec_id)

@router.post("/{rec_id}/reject", response_model=Recommendation)
async def reject_recommendation(rec_id: str):
    return await recommendation_service.reject(rec_id)

@router.post("/{rec_id}/apply", response_model=Recommendation)
async def apply_recommendation(rec_id: str):
    return await recommendation_service.apply(rec_id)

@router.post("/{rec_id}/rollback", response_model=Recommendation)
async def rollback_recommendation(rec_id: str):
    return await recommendation_service.rollback(rec_id)
