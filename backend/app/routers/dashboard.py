from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.campaign import Campaign
from app.models.job import Job
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate numbers for the dashboard header strip (architecture doc,
    section 6). See the accompanying note for which table backs each
    field — short version: the three totals are summed off campaigns'
    running counters, the two job counts come straight from jobs.status.
    """
    totals = db.query(
        func.coalesce(func.sum(Campaign.total_scraped), 0),
        func.coalesce(func.sum(Campaign.total_enriched), 0),
        func.coalesce(func.sum(Campaign.total_imported), 0),
    ).one()
    total_scraped, total_enriched, total_imported = totals

    active_jobs = (
        db.query(func.count(Job.id)).filter(Job.status.in_(["PENDING", "RUNNING"])).scalar()
    )
    failed_jobs = db.query(func.count(Job.id)).filter(Job.status == "FAILED").scalar()

    return DashboardStats(
        total_scraped=total_scraped,
        total_enriched=total_enriched,
        total_imported=total_imported,
        active_jobs=active_jobs,
        failed_jobs=failed_jobs,
    )
