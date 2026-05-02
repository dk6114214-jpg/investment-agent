from fastapi import UploadFile, File
import pandas as pd

@app.post("/recommendation")
async def recommend(
    file: UploadFile = File(...),
    data: dict = {}
):

    # -----------------------
    # 1. FORCE FILE CHECK
    # -----------------------
    if file is None:
        return {
            "error": "CSV file is required. Upload market data first."
        }

    # -----------------------
    # 2. READ CSV
    # -----------------------
    df = pd.read_csv(file.file)

    if df.empty:
        return {
            "error": "CSV is empty. Please upload valid market data."
        }

    # -----------------------
    # 3. USER INPUTS
    # -----------------------
    risk = data.get("risk_preference", "Medium")
    investment = data.get("investment_amount", 100000)

    # -----------------------
    # 4. RISK LOGIC
    # -----------------------
    if risk == "Low":
        weights = [0.6, 0.25, 0.15]
    elif risk == "High":
        weights = [0.4, 0.35, 0.25]
    else:
        weights = [0.5, 0.3, 0.2]

    # -----------------------
    # 5. BUILD PORTFOLIO FROM FILE ONLY
    # -----------------------
    portfolio = []

    records = df.to_dict(orient="records")

    for i, stock in enumerate(records[:3]):
        portfolio.append({
            "symbol": stock.get("symbol"),
            "sector": stock.get("sector"),
            "allocation_%": round(weights[i] * 100, 2),
            "amount": round(investment * weights[i], 2)
        })

    return {
        "risk_used": risk,
        "portfolio": portfolio,
        "message": "Generated ONLY from uploaded CSV file"
    }