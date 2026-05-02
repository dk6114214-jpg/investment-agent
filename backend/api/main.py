from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI()

# -----------------------
# CORS (Frontend connection safe)
# -----------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# HEALTH CHECK
# -----------------------
@app.get("/")
def home():
    return {
        "status": "AI Investment Portfolio API is running"
    }

# -----------------------
# MARKET UPLOAD (optional storage not used)
# -----------------------
@app.post("/market/upload")
async def upload_market(file: UploadFile = File(...)):

    if not file:
        raise HTTPException(status_code=400, detail="File required")

    df = pd.read_csv(file.file)

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV is empty")

    return {
        "message": "Market file received successfully",
        "rows": len(df)
    }

# -----------------------
# RECOMMENDATION (STRICT FILE BASED)
# -----------------------
@app.post("/recommendation")
async def recommend(file: UploadFile = File(...), data: dict = {}):

    if not file:
        raise HTTPException(
            status_code=400,
            detail="CSV file is required"
        )

    df = pd.read_csv(file.file)

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV is empty")

    # -----------------------
    # USER INPUTS
    # -----------------------
    risk = data.get("risk_preference", "Medium")
    investment = data.get("investment_amount", 100000)

    # -----------------------
    # RISK WEIGHTS
    # -----------------------
    if risk == "Low":
        weights = [0.6, 0.3, 0.1]
    elif risk == "High":
        weights = [0.4, 0.35, 0.25]
    else:
        weights = [0.5, 0.3, 0.2]

    # -----------------------
    # BUILD PORTFOLIO FROM CSV ONLY
    # -----------------------
    records = df.to_dict(orient="records")

    portfolio = []

    for i, stock in enumerate(records[:3]):
        portfolio.append({
            "symbol": stock.get("symbol", "N/A"),
            "sector": stock.get("sector", "N/A"),
            "allocation_%": round(weights[i] * 100, 2),
            "amount": round(investment * weights[i], 2)
        })

    return {
        "risk_used": risk,
        "portfolio": portfolio,
        "message": "Generated ONLY from uploaded CSV"
    }

# -----------------------
# RESET (stateless system)
# -----------------------
@app.get("/reset")
def reset():
    return {
        "message": "Stateless API - no memory stored"
    }