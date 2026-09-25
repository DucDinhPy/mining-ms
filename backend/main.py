from fastapi import FastAPI
from backend.routers import ppe


app = FastAPI(title="MiningProject API")

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

    
app.include_router(ppe.router)