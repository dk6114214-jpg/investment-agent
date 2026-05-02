import pandas as pd
from fastapi import FastAPI, UploadFile, File

app = FastAPI()

# ------------------------
# MEMORY STORAGE
# ------------------------
market_data = []
research_data = []

# ------------------------
# HOME
# ------------------------
@app.get("/")
def home():
    return {
        "status": "AI Investment Portfolio API is running",
        "market_rows": len(market_data),
        "research_rows": len(research_data)
    }

# ------------------------
# UPLOAD MARKET CSV
# ------------------------
@app.post("/market/upload")
async def upload_market(file: UploadFile = File(...)):
    global market_data

    df = pd.read_csv(file.file)
    market_data = df.to_dict(orient="records")

    return {
        "message": "Market uploaded successfully",
        "rows": len(market_data)
    }

# ------------------------
# RECOMMENDATION ENGINE (MAIN FIX)
# ------------------------
@app.post("/recommendation")
def recommend(data: dict):

    if len(market_data) == 0:
        return {"error": "Please upload market CSV first"}

    risk = data.get("risk_preference", "Medium")
    investment = data.get("investment_amount", 100000)

    portfolio = []

    # risk-based allocation logic
    if risk == "Low":
        weights = [0.50, 0.30, 0.20]
    elif risk == "High":
        weights = [0.40, 0.35, 0.25]
    else:
        weights = [0.45, 0.30, 0.25]

    # select top 3-5 stocks from uploaded file
    selected_stocks = market_data[:3]

    for i, stock in enumerate(selected_stocks):
        weight = weights[i] if i < len(weights) else 0.1

        portfolio.append({
            "symbol": stock.get("symbol"),
            "sector": stock.get("sector", "Unknown"),
            "price": stock.get("price", 0),
            "allocation_percent": round(weight * 100, 2),
            "allocated_amount": round(investment * weight, 2)
        })

    return {
        "risk_used": risk,
        "total_investment": investment,
        "portfolio": portfolio,
        "message": "Recommendation generated from uploaded CSV"
    }

# ------------------------
# RESEARCH UPLOAD (optional)
# ------------------------
@app.post("/equity-reports/upload")
async def upload_research(file: UploadFile = File(...)):
    global research_data

    df = pd.read_csv(file.file)
    research_data = df.to_dict(orient="records")

    return {
        "message": "Research uploaded successfully",
        "rows": len(research_data)
    }