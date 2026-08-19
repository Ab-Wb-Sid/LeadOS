from pydantic import BaseModel


class DashboardStats(BaseModel):
    """Response shape for GET /dashboard/stats — matches the top strip of
    the dashboard wireframe (architecture doc, section 6):

        Total Scraped: 4,210   Enriched: 2,980   Imported: 2,100
        Active Jobs: 2          Failed Jobs: 1
    """

    total_scraped: int
    total_enriched: int
    total_imported: int
    active_jobs: int
    failed_jobs: int
