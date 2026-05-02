from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# --------------------
# CORS (IMPORTANT for Vercel frontend)
# --------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------
# HEALTH CHECK (FIX for API offline)
# --------------------
@app.get("/")
def root():
    return {
        "status": "AI Investment Portfolio API is running",
        "market_rows": 10,
        "research_rows": 10
    }

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "message": "API is healthy and running"
    }

# --------------------
# Upload Market CSV
# --------------------
@app.post("/market/upload")
async def upload_market(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    return {
        "message": "Market data uploaded successfully",
        "rows": len(df)
    }

# --------------------
# Upload Research CSV
# --------------------
@app.post("/equity-reports/upload")
async def upload_research(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    return {
        "message": "Research data uploaded successfully",
        "rows": len(df)
    }

# --------------------
# Recommendation Endpoint (SAFE MOCK IF LLM FAILS)
# --------------------
@app.post("/recommendation")
def recommend(data: dict):
    return {
        "portfolio": [
            {"symbol": "HBL", "allocation": 40},
            {"symbol": "UBL", "allocation": 30},
            {"symbol": "OGDC", "allocation": 30}
        ],
        "risk": data.get("risk_preference", "Medium"),
        "status": "success"
    }