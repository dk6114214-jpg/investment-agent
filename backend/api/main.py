from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]
DEFAULT_MARKET_FILE = BASE_DIR / "psx_market.csv"
DEFAULT_RESEARCH_FILE = BASE_DIR / "psx_research.csv"
FRONTEND_BUILD_DIR = PROJECT_DIR / "frontend" / "web" / "build"

DEFAULT_SECTORS = {
    "HBL": "Banking",
    "ABL": "Banking",
    "MCB": "Banking",
    "UBL": "Banking",
    "BAFL": "Banking",
    "ENGRO": "Fertilizer",
    "LUCK": "Cement",
    "PSO": "Oil & Gas",
    "OGDC": "Oil & Gas",
    "KAPCO": "Power",
}


class InvestorProfile(BaseModel):
    age: int = Field(default=25, ge=18, le=100)
    income: float = Field(default=100000, ge=0)
    investment_amount: float = Field(default=20000, gt=0)
    risk_preference: Literal["Low", "Medium", "High"] = "Medium"
    financial_goals: str = "Wealth growth"
    time_period_years: int = Field(default=5, ge=1, le=50)


app = FastAPI(title="AI Investment Portfolio Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files if they exist
if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")

market_df: pd.DataFrame | None = None
research_df: pd.DataFrame | None = None


def _read_csv_upload(file: UploadFile) -> pd.DataFrame:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file.")

    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to read CSV file.") from exc

    if df.empty:
        raise HTTPException(status_code=400, detail="Uploaded CSV is empty.")

    df.columns = [str(column).strip() for column in df.columns]
    return df


def _load_default_data() -> None:
    global market_df, research_df

    if DEFAULT_MARKET_FILE.exists():
        market_df = pd.read_csv(DEFAULT_MARKET_FILE)

    if DEFAULT_RESEARCH_FILE.exists():
        research_df = pd.read_csv(DEFAULT_RESEARCH_FILE)


@app.on_event("startup")
def startup() -> None:
    _load_default_data()


def _status_payload():
    return {
        "status": "AI Investment Portfolio API is running",
        "market_rows": 0 if market_df is None else len(market_df),
        "research_rows": 0 if research_df is None else len(research_df),
    }


@app.get("/api/health")
def health():
    return _status_payload()


@app.get("/")
def home():
    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)

    return _status_payload()


@app.post("/market/upload")
def upload_market(file: UploadFile = File(...)):
    global market_df

    df = _read_csv_upload(file)
    if "symbol" not in df.columns:
        raise HTTPException(status_code=400, detail="Market CSV must include a symbol column.")

    market_df = df
    return {"status": "market uploaded", "rows": len(market_df)}


@app.post("/equity-reports/upload")
def upload_research(file: UploadFile = File(...)):
    global research_df

    df = _read_csv_upload(file)
    if "symbol" not in df.columns:
        raise HTTPException(status_code=400, detail="Research CSV must include a symbol column.")

    research_df = df
    return {"status": "research uploaded", "rows": len(research_df)}


def _minmax(series: pd.Series, default: float = 0.5) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.notna().sum() == 0:
        return pd.Series(default, index=series.index)

    spread = values.max() - values.min()
    if pd.isna(spread) or abs(spread) < 1e-12:
        return pd.Series(default, index=series.index)

    return ((values - values.min()) / spread).fillna(default).clip(0, 1)


def _first_existing_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lookup = {column.lower().replace(" ", "_"): column for column in df.columns}
    for candidate in candidates:
        found = lookup.get(candidate.lower().replace(" ", "_"))
        if found:
            return found
    return None


def _prepare_assets(df: pd.DataFrame) -> pd.DataFrame:
    if "symbol" not in df.columns:
        raise HTTPException(status_code=400, detail="Market data must include a symbol column.")

    work = df.copy()
    work["symbol"] = work["symbol"].astype(str).str.strip()
    work = work[work["symbol"] != ""]

    if work.empty:
        raise HTTPException(status_code=400, detail="Market data does not contain valid symbols.")

    if "price" in work.columns:
        work["price"] = pd.to_numeric(work["price"], errors="coerce")
        work = work.dropna(subset=["price"])

    volume_col = _first_existing_column(work, ["volume", "turnover", "traded_volume"])
    sector_col = _first_existing_column(work, ["sector", "industry"])

    rows = []
    for symbol, group in work.groupby("symbol", sort=True):
        group = group.copy()

        if "timestamp" in group.columns:
            group["timestamp"] = pd.to_datetime(group["timestamp"], errors="coerce")
            group = group.sort_values("timestamp")

        if volume_col:
            volume = float(pd.to_numeric(group[volume_col], errors="coerce").mean())
        else:
            volume = 0.0

        if "return" in group.columns:
            return_series = pd.to_numeric(group["return"], errors="coerce").dropna()
            market_return = float(return_series.mean()) if not return_series.empty else np.nan
        elif "price" in group.columns and len(group["price"].dropna()) > 1:
            prices = group["price"].dropna()
            market_return = float((prices.iloc[-1] - prices.iloc[0]) / max(prices.iloc[0], 1e-9))
        else:
            market_return = np.nan

        if "price" in group.columns and len(group["price"].dropna()) > 2:
            pct_change = group["price"].dropna().pct_change().dropna()
            volatility = float(pct_change.std()) if not pct_change.empty else 0.03
        else:
            volatility = np.nan

        if sector_col:
            sector = str(group[sector_col].dropna().iloc[-1]) if group[sector_col].notna().any() else "Unknown"
        else:
            sector = DEFAULT_SECTORS.get(symbol.upper(), "Unknown")

        rows.append(
            {
                "symbol": symbol,
                "sector": sector,
                "market_return": market_return,
                "volatility": volatility,
                "volume": volume,
            }
        )

    if not rows:
        raise HTTPException(status_code=400, detail="Market data could not be converted into assets.")

    assets = pd.DataFrame(rows)

    assets["liquidity_score"] = _minmax(assets["volume"])
    assets["fundamental_score"] = 0.5
    assets["confidence_score"] = 0.5

    if research_df is not None and "symbol" in research_df.columns:
        research = research_df.copy()
        research["symbol"] = research["symbol"].astype(str).str.strip()
        score_columns = [column for column in research.columns if "score" in column.lower()]
        if score_columns:
            score_col = score_columns[0]
            research[score_col] = pd.to_numeric(research[score_col], errors="coerce")
            scores = research.groupby("symbol", as_index=False)[score_col].mean()
            assets = assets.merge(scores, on="symbol", how="left")
            assets["fundamental_score"] = assets[score_col].fillna(0.5).clip(0, 1)

        confidence_col = _first_existing_column(research, ["confidence", "analyst_confidence"])
        if confidence_col:
            research[confidence_col] = pd.to_numeric(research[confidence_col], errors="coerce")
            confidence = research.groupby("symbol", as_index=False)[confidence_col].mean()
            assets = assets.merge(confidence, on="symbol", how="left")
            assets["confidence_score"] = assets[confidence_col].fillna(0.5).clip(0, 1)

    return_col = _first_existing_column(assets, ["market_return"])
    assets["market_return_score"] = _minmax(assets[return_col]) if return_col else 0.5

    fallback_return = (
        0.035
        + assets["fundamental_score"] * 0.09
        + assets["confidence_score"] * 0.025
        + assets["liquidity_score"] * 0.025
    )
    assets["expected_return"] = pd.to_numeric(assets["market_return"], errors="coerce").fillna(fallback_return)
    assets["expected_return"] = assets["expected_return"].clip(lower=0.005, upper=0.30)

    fallback_volatility = (
        0.08
        + (1 - assets["fundamental_score"]) * 0.08
        + (1 - assets["liquidity_score"]) * 0.05
        + (1 - assets["confidence_score"]) * 0.03
    )
    assets["volatility"] = pd.to_numeric(assets["volatility"], errors="coerce").fillna(fallback_volatility)
    assets["volatility"] = assets["volatility"].clip(lower=0.02, upper=0.45)

    assets["return_score"] = _minmax(assets["expected_return"])
    assets["risk_score"] = 1 - _minmax(assets["volatility"])

    return assets


def _normalize_weights(raw_weights: np.ndarray, max_weight: float) -> np.ndarray:
    weights = raw_weights / raw_weights.sum()

    for _ in range(12):
        overflow = np.maximum(weights - max_weight, 0)
        if overflow.sum() <= 1e-9:
            break

        weights = np.minimum(weights, max_weight)
        room = np.maximum(max_weight - weights, 0)
        if room.sum() <= 1e-9:
            break
        weights = weights + room / room.sum() * overflow.sum()

    return weights / weights.sum()


def _select_diversified_assets(assets: pd.DataFrame, top_n: int = 5, sector_limit: int = 2) -> pd.DataFrame:
    selected = []
    sector_counts: dict[str, int] = {}

    for _, row in assets.sort_values(by="investor_score", ascending=False).iterrows():
        sector = str(row["sector"])
        if sector_counts.get(sector, 0) >= sector_limit:
            continue
        selected.append(row)
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        if len(selected) == top_n:
            break

    if len(selected) < top_n:
        selected_symbols = {row["symbol"] for row in selected}
        for _, row in assets.sort_values(by="investor_score", ascending=False).iterrows():
            if row["symbol"] in selected_symbols:
                continue
            selected.append(row)
            if len(selected) == top_n:
                break

    return pd.DataFrame(selected)


def compute_portfolio(df: pd.DataFrame, user: InvestorProfile) -> pd.DataFrame:
    assets = _prepare_assets(df)
    settings = {
        "Low": {
            "return_weight": 0.25,
            "fundamental_weight": 0.30,
            "liquidity_weight": 0.20,
            "risk_weight": 0.25,
            "temperature": 0.035,
            "max_weight": 0.28,
            "reason": "capital preservation with liquidity and fundamentals",
        },
        "Medium": {
            "return_weight": 0.38,
            "fundamental_weight": 0.27,
            "liquidity_weight": 0.15,
            "risk_weight": 0.20,
            "temperature": 0.045,
            "max_weight": 0.34,
            "reason": "balanced return, risk, liquidity, and fundamentals",
        },
        "High": {
            "return_weight": 0.52,
            "fundamental_weight": 0.22,
            "liquidity_weight": 0.08,
            "risk_weight": 0.18,
            "temperature": 0.055,
            "max_weight": 0.46,
            "reason": "growth-seeking with a controlled risk penalty",
        },
    }
    config = settings[user.risk_preference]

    age_risk_tilt = max(min((35 - user.age) / 100, 0.12), -0.18)
    horizon_risk_tilt = max(min((user.time_period_years - 5) / 80, 0.18), -0.08)
    risk_capacity_tilt = age_risk_tilt + horizon_risk_tilt

    return_weight = max(0.15, config["return_weight"] + risk_capacity_tilt)
    risk_weight = max(0.08, config["risk_weight"] - risk_capacity_tilt)

    assets["investor_score"] = (
        assets["return_score"] * return_weight
        + assets["fundamental_score"] * config["fundamental_weight"]
        + assets["liquidity_score"] * config["liquidity_weight"]
        + assets["risk_score"] * risk_weight
    )

    selected = _select_diversified_assets(assets).copy()
    raw_scores = selected["investor_score"].to_numpy(dtype=float)
    raw_weights = np.exp((raw_scores - raw_scores.max()) / config["temperature"])
    weights = _normalize_weights(raw_weights, config["max_weight"])

    selected["allocation_pct"] = weights * 100
    selected["score"] = selected["investor_score"] * 100
    selected["strategy_reason"] = config["reason"]
    selected["return_weight"] = return_weight
    selected["risk_weight"] = risk_weight

    return selected.sort_values(by="allocation_pct", ascending=False)


@app.post("/recommendation")
def recommend(user: InvestorProfile):
    if market_df is None:
        raise HTTPException(status_code=400, detail="Upload market data first.")

    result = compute_portfolio(market_df.copy(), user)

    portfolio = []
    for _, row in result.iterrows():
        portfolio.append(
            {
                "symbol": row["symbol"],
                "allocation_pct": round(float(row["allocation_pct"]), 2),
                "score": round(float(row["score"]), 2),
                "sector": row["sector"],
                "reasons": [
                    row["strategy_reason"].capitalize(),
                    f"Expected return: {round(float(row['expected_return']) * 100, 2)}%",
                    f"Volatility estimate: {round(float(row['volatility']) * 100, 2)}%",
                    f"FA score: {round(float(row['fundamental_score']) * 100, 1)}%",
                    f"Liquidity score: {round(float(row['liquidity_score']) * 100, 1)}%",
                    f"Risk profile: {user.risk_preference}",
                ],
            }
        )

    return {
        "model": "MULTI_FACTOR_INVESTOR_POLICY_V5",
        "methodology": (
            "Scores each stock using expected return, volatility risk, fundamental score, "
            "liquidity, confidence, and sector diversification. Investor age, horizon, "
            "and risk preference change the return-vs-risk weights."
        ),
        "investment_amount": user.investment_amount,
        "portfolio": portfolio,
    }


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    requested_file = FRONTEND_BUILD_DIR / full_path
    index_file = FRONTEND_BUILD_DIR / "index.html"

    if requested_file.is_file():
        return FileResponse(requested_file)

    if index_file.is_file():
        return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Frontend build not found.")
