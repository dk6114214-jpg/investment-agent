import pandas as pd
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

# -----------------------
# HOME (NO MEMORY DATA)
# -----------------------
@app.get("/")
def home():
    return {
        "status": "AI Investment Portfolio API is running",
        "message": "Upload CSV to get recommendations"
    }

# -----------------------
# MARKET UPLOAD (ONLY SOURCE OF DATA)
# -----------------------
@app.post("/market/upload")
async def upload_market(file: UploadFile = File(...)):

    df = pd.read_csv(file.file)

    if df.empty:
        return {"error": "CSV is empty"}

    # return ONLY processed data (NO GLOBAL STORAGE)
    return {
        "message": "File received successfully",
        "rows": len(df),
        "preview": df.head(3).to_dict(orient="records")
    }

# -----------------------
# RECOMMENDATION (USES FILE ONLY)
# -----------------------
@app.post("/recommendation")
async def recommend(file: UploadFile = File(...), data: dict = {}):

    df = pd.read_csv(file.file)

    if df.empty:
        return {"error": "CSV is empty"}

    risk = data.get("risk_preference", "Medium")
    investment = data.get("investment_amount", 100000)

    if risk == "Low":
        weights = [0.6, 0.25, 0.15]
    elif risk == "High":
        weights = [0.4, 0.35, 0.25]
    else:
        weights = [0.5, 0.3, 0.2]

    portfolio = []

    for i, stock in enumerate(df.head(3).to_dict(orient="records")):
        portfolio.append({
            "symbol": stock.get("symbol", "N/A"),
            "sector": stock.get("sector", "Unknown"),
            "allocation_%": round(weights[i] * 100, 2),
            "amount": round(investment * weights[i], 2)
        })

    return {
        "risk_used": risk,
        "portfolio": portfolio,
        "message": "Generated ONLY from uploaded file"
    }