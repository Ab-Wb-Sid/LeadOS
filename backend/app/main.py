from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import apify_accounts, apollo_accounts, auth, campaigns, dashboard

app = FastAPI(title="LeadOS API")

# Next.js frontend runs on localhost:3000 in dev (see docker-compose.yml).
# allow_credentials=True is required for the httpOnly auth cookie to be
# sent/received cross-origin — and per the CORS spec, allow_origins can't
# be "*" when credentials are allowed, so this must be an explicit list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(campaigns.router)
app.include_router(dashboard.router)
app.include_router(apify_accounts.router)
app.include_router(apollo_accounts.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is healthy"}
