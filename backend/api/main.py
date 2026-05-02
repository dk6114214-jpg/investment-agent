import pandas as pd
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

# -----------------------
# GLOBAL STORAGE
# -----------------------
market_data = []
research_data = []

# -----------------------
# HOME
# -----------------------
@app.get("/")
def home():
    return {
        "status": "AI Investment Portfolio API is running",
        "market_uploaded": len(market_data) > 0,
        "market_rows": len(market_data),
        "research_rows": len(research_data)
    }

# -----------------------
# MARKET UPLOAD
# -----------------------
@app.post("/market/upload")
async def upload_market(file: UploadFile = File(...)):
    global market_data

    df = pd.read_csv(file.file)

    if df.empty:
        return {"error": "CSV is empty"}

    market_data = df.to_dict(orient="records")

    return {
        "message": "Market uploaded successfully",
        "rows": len(market_data)
    }

# -----------------------
# RECOMMENDATION
# -----------------------
@app.post("/recommendation")
def recommend(data: dict):

    if len(market_data) == 0:
        return {
            "error": "No market data uploaded. Please upload CSV first."
        }

    risk = data.get("risk_preference", "Medium")
    investment = data.get("investment_amount", 100000)

    # risk logic
    if risk == "Low":
        weights = [0.60, 0.25, 0.15]
    elif risk == "High":
        weights = [0.40, 0.35, 0.25]
    else:
        weights = [0.50, 0.30, 0.20]

    portfolio = []

    # dynamic use of CSV (NOT FIXED STOCKS)
    for i, stock in enumerate(market_data[:3]):
        portfolio.append({
            "symbol": stock.get("symbol", "N/A"),
            "sector": stock.get("sector", "Unknown"),
            "allocation_%": round(weights[i] * 100, 2),
            "amount": round(investment * weights[i], 2)
        })

    return {
        "risk_used": risk,
        "portfolio": portfolio,
        "message": "Generated ONLY from uploaded CSV"
    }

# -----------------------
# RESET (FIXED)
# -----------------------
@app.get("/reset")
def reset():
    global market_data, research_data
    market_data = []
    research_data = []

    return {
        "message": "reset done",
        "market_rows": 0,
        "research_rows": 0
    }