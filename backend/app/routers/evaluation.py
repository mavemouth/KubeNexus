from fastapi import APIRouter, HTTPException
from typing import List

from app.models.schemas import PostChangeEvaluation
from app.storage.db import db

router = APIRouter(prefix="/evaluations", tags=["Post-Change Evaluation"])

@router.get("", response_model=List[PostChangeEvaluation])
def get_evaluations():
    return db.get_all_evaluations()

@router.get("/workload/{workload_id}", response_model=List[PostChangeEvaluation])
def get_workload_evaluations(workload_id: str):
    evals = [e for e in db.get_all_evaluations() if e.workloadId == workload_id or e.workloadName == workload_id]
    return evals
