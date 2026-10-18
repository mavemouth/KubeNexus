from fastapi import APIRouter
from app.models.schemas import CostOptimizationSummary
from app.storage.db import db

router = APIRouter(prefix="/cost", tags=["Cost Optimization"])

def calc_resource_cost(cpu_cores: float, memory_mb: float) -> float:
    """Standard cloud rate: $0.04/core/hr + $0.005/GB/hr * 730 hrs"""
    hourly = (cpu_cores * 0.04) + ((memory_mb / 1024.0) * 0.005)
    return round(hourly * 730, 2)

@router.get("/summary", response_model=CostOptimizationSummary)
def get_cost_summary():
    workloads = db.get_all_workloads()
    recommendations = db.get_all_recommendations()

    # Calculate total current cloud compute spend
    total_spend = sum(
        calc_resource_cost(w.cpuRequestCores, w.memoryRequestMb)
        for w in workloads
    )

    # Calculate potential savings from positive recommendations
    potential_savings = sum(
        r.estimatedMonthlySavings for r in recommendations
        if r.status in ["Generated", "Approved"] and r.estimatedMonthlySavings > 0
    )

    optimized_spend = max(0.0, total_spend - potential_savings)
    savings_pct = round((potential_savings / total_spend * 100.0) if total_spend > 0 else 0.0, 1)

    over_count = len([w for w in workloads if w.status == "Over-provisioned"])
    under_count = len([w for w in workloads if w.status == "Under-provisioned"])

    return CostOptimizationSummary(
        monthlySpend=round(total_spend, 2),
        potentialSavings=round(potential_savings, 2),
        optimizedSpend=round(optimized_spend, 2),
        savingsPct=savings_pct,
        overProvisionedCount=over_count,
        underProvisionedCount=under_count
    )
