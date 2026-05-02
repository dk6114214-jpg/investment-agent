import pandas as pd
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

market_data = []

# -----------------------
# HOME
# -----------------------
@app.get("/")
def home():
    return {
        "status": "AI Investment Portfolio API is running",
        "market_uploaded": len(market_data) > 0,
        "rows": len(market_data)
    }

# -----------------------
# MARKET UPLOAD (REQUIRED)
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
# RECOMMENDATION (STRICT)
# -----------------------
@app.post("/recommendation")
def recommend(data: dict):

    # ❌ BLOCK IF NO FILE UPLOADED
    if len(market_data) == 0:
        return {
            "error": "No market data uploaded. Please upload CSV first."
        }

    risk = data.get("risk_preference", "Medium")
    investment = data.get("investment_amount", 100000)

    # risk weights
    if risk == "Low":
        weights = [0.60, 0.25, 0.15]
    elif risk == "High":
        weights = [0.40, 0.35, 0.25]
    else:
        weights = [0.50, 0.30, 0.20]

    portfolio = []

    stocks = market_data[:3]

    for i, stock in enumerate(stocks):
        portfolio.append({
            "symbol": stock["symbol"],
            "sector": stock.get("sector"),
            "allocation_%": round(weights[i] * 100, 2),
            "amount": round(investment * weights[i], 2)
        })

    return {
        "risk_used": risk,
        "portfolio": portfolio,
        "message": "Generated ONLY from uploaded CSV"
    }