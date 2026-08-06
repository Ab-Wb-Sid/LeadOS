from fastapi import FastAPI

app = FastAPI(title="LeadOS API")

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "Backend is healthy"}
