from pathlib import Path
from typing import Literal
import json
import os
import subprocess

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]
FRONTEND_BUILD_DIR = PROJECT_DIR / "frontend" / "web" / "build"

app = FastAPI(title="PSX Portfolio Optimizer")

market_df_cache: pd.DataFrame | None = None
research_df_cache: pd.DataFrame | None = None

frontend_origins = [
    origin.strip()
    for origin in os.getenv("FRONTEND_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        *frontend_origins,
    ],
    allow_origin_regex=r"https://.*\.(onrender\.com|vercel\.app)$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if FRONTEND_BUILD_DIR.exists():
    app.mount("/static", StaticFiles(directory=FRONTEND_BUILD_DIR / "static"), name="static")


class InvestorProfile(BaseModel):
    age: int = Field(default=25, ge=18, le=100)
    income: float = Field(default=100000, ge=0)
    investment_amount: float = Field(default=20000, gt=0)
    risk_preference: Literal["Low", "Medium", "High"] = "Medium"
    financial_goals: str = "Wealth growth"
    time_period_years: int = Field(default=5, ge=1, le=50)


def _get_deployment_version() -> str:
    env_version = os.getenv("COMMIT_SHA") or os.getenv("GIT_COMMIT")
    if env_version:
        return env_version
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_DIR),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def _status_payload() -> dict:
    return {
        "status": "AI Investment Portfolio API is running",
        "market_rows": 0 if market_df_cache is None else len(market_df_cache),
        "research_rows": 0 if research_df_cache is None else len(research_df_cache),
        "data_loaded": market_df_cache is not None,
        "version": _get_deployment_version(),
    }


def _normalize(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.empty or values.nunique(dropna=True) <= 1:
        return pd.Series(0.5, index=series.index)
    scaled = (values - values.min()) / (values.max() - values.min())
    return scaled.fillna(0.5).clip(0, 1)


def _normalize_symbol(value) -> str:
    return str(value or "").split(".")[0].strip().upper()


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned.columns = [str(col).strip() for col in cleaned.columns]
    if "symbol" not in cleaned.columns:
        raise HTTPException(status_code=400, detail="CSV must include a symbol column")
    cleaned["symbol"] = cleaned["symbol"].map(_normalize_symbol)
    return cleaned


async def _read_upload_csv(file: UploadFile, label: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Unable to read {label} CSV") from exc

    if df.empty:
        raise HTTPException(status_code=400, detail=f"{label.title()} CSV is empty")

    return _clean_columns(df)


def _prepare_assets_for_recommendation(market_df: pd.DataFrame, research_df: pd.DataFrame | None) -> pd.DataFrame:
    if market_df is None or market_df.empty:
        raise HTTPException(status_code=400, detail="No market data available")

    assets = market_df.copy()
    assets["sector"] = assets["sector"].astype(str).fillna("Unknown") if "sector" in assets.columns else "Unknown"
    assets["price"] = pd.to_numeric(assets.get("price", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    assets["volume"] = pd.to_numeric(assets.get("volume", pd.Series(dtype=float)), errors="coerce").fillna(0.0)

    if research_df is not None and not research_df.empty and "symbol" in research_df.columns:
        research = research_df.copy()
        score_col = next((col for col in research.columns if "score" in col.lower()), None)
        confidence_col = next((col for col in research.columns if "confidence" in col.lower()), None)
        keep_cols = ["symbol"]
        if score_col:
            research[score_col] = pd.to_numeric(research[score_col], errors="coerce")
            keep_cols.append(score_col)
        if confidence_col:
            research[confidence_col] = pd.to_numeric(research[confidence_col], errors="coerce")
            keep_cols.append(confidence_col)
        if len(keep_cols) > 1:
            research = research[keep_cols].drop_duplicates(subset=["symbol"])
            assets = assets.merge(research, on="symbol", how="left")

    assets["fundamental_score"] = _normalize(
        assets.get("FA Score", assets.get("fundamental_score", pd.Series(0.5, index=assets.index)))
    )
    assets["confidence_score"] = _normalize(
        assets.get("Confidence", assets.get("confidence_score", pd.Series(0.5, index=assets.index)))
    )
    assets["liquidity_score"] = _normalize(assets["volume"])
    assets["price_score"] = _normalize(assets["price"])

    assets["expected_return"] = (
        0.04
        + assets["fundamental_score"] * 0.14
        + assets["confidence_score"] * 0.05
        + assets["price_score"] * 0.03
    ).clip(0.03, 0.32)

    assets["volatility"] = (
        0.28
        - assets["fundamental_score"] * 0.10
        - assets["confidence_score"] * 0.05
        + (1 - assets["liquidity_score"]) * 0.10
    ).clip(0.06, 0.40)

    assets["sharpe_ratio"] = assets["expected_return"] / assets["volatility"]
    assets["sharpe_score"] = _normalize(assets["sharpe_ratio"])
    assets["return_score"] = _normalize(assets["expected_return"])
    assets["risk_score"] = 1 - _normalize(assets["volatility"])

    assets["raw_score"] = (
        assets["return_score"] * 0.35
        + assets["risk_score"] * 0.25
        + assets["sharpe_score"] * 0.20
        + assets["fundamental_score"] * 0.10
        + assets["confidence_score"] * 0.06
        + assets["liquidity_score"] * 0.04
    )
    return assets


def _normalize_weights(values: np.ndarray, max_weight: float) -> np.ndarray:
    weights = np.maximum(values.copy(), 0)
    if weights.sum() <= 0:
        weights = np.ones_like(weights)
    weights = weights / weights.sum()
    weights = np.minimum(weights, max_weight)
    return weights / weights.sum()


def _strategy_reason(risk: str) -> str:
    if risk == "Low":
        return "Capital preservation with liquidity and fundamentals"
    if risk == "High":
        return "Growth-seeking with a controlled risk penalty"
    return "Balanced return, risk, liquidity, and fundamentals"


def _format_portfolio(assets: pd.DataFrame, weights: np.ndarray, profile: InvestorProfile) -> list[dict]:
    assets = assets.copy()
    assets["allocation_pct"] = np.round(weights * 100, 2)
    portfolio = []

    for _, row in assets.iterrows():
        allocation = float(row["allocation_pct"])
        portfolio.append(
            {
                "symbol": row["symbol"],
                "sector": row["sector"],
                "allocation_pct": allocation,
                "amount": round(profile.investment_amount * (allocation / 100), 2),
                "score": round(float(row["raw_score"] * 100), 2),
                "expected_return": round(float(row["expected_return"] * 100), 2),
                "volatility": round(float(row["volatility"] * 100), 2),
                "sharpe_ratio": round(float(row["sharpe_ratio"]), 2),
                "fundamental_score": round(float(row["fundamental_score"] * 100), 1),
                "liquidity_score": round(float(row["liquidity_score"] * 100), 1),
                "confidence_score": round(float(row["confidence_score"] * 100), 1),
                "reasons": [
                    _strategy_reason(profile.risk_preference),
                    f"Expected return: {float(row['expected_return'] * 100):.2f}%",
                    f"Volatility estimate: {float(row['volatility'] * 100):.2f}%",
                    f"FA score: {float(row['fundamental_score'] * 100):.1f}%",
                    f"Liquidity score: {float(row['liquidity_score'] * 100):.1f}%",
                    f"Risk profile: {profile.risk_preference}",
                ],
            }
        )
    return portfolio


def _recommend_from_data(market_df: pd.DataFrame, research_df: pd.DataFrame | None, profile: InvestorProfile) -> dict:
    assets = _prepare_assets_for_recommendation(market_df, research_df)
    if assets.empty:
        raise HTTPException(status_code=400, detail="No asset data available")

    if profile.risk_preference == "Low":
        scores = assets["raw_score"] * 0.8 + assets["risk_score"] * 0.25
        max_weight = 0.28
    elif profile.risk_preference == "High":
        scores = assets["raw_score"] * 1.05 + assets["return_score"] * 0.3
        max_weight = 0.42
    else:
        scores = assets["raw_score"]
        max_weight = 0.34

    assets = assets.copy()
    assets["investor_score"] = _normalize(scores)
    assets = assets.sort_values(by="investor_score", ascending=False)

    selected = assets.head(5)
    weights = _normalize_weights(selected["investor_score"].values, max_weight=max_weight)
    portfolio = _format_portfolio(selected, weights, profile)

    return {
        "model": "DATA_DRIVEN_PORTFOLIO_V2",
        "risk_preference": profile.risk_preference,
        "investment_amount": profile.investment_amount,
        "portfolio": portfolio,
        "metrics": {
            "total_symbols": int(assets["symbol"].nunique()),
            "recommended_symbols": len(portfolio),
            "research_coverage": "Uploaded" if research_df is not None else "--",
            "average_score": round(sum(item["score"] for item in portfolio) / len(portfolio), 2),
        },
        "methodology": (
            "Scores each stock using expected return, volatility risk, fundamental score, "
            "liquidity, confidence, and sector diversification. Investor age, horizon, "
            "and risk preference change the return-vs-risk weights."
        ),
    }


@app.get("/api/health")
def health():
    return {"status": "ok", **_status_payload()}


@app.get("/api/version")
def version():
    return {"version": _get_deployment_version()}


@app.get("/")
def home():
    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file, media_type="text/html")
    return _status_payload()


@app.post("/market/upload")
async def upload_market(file: UploadFile = File(...)):
    global market_df_cache
    market_df_cache = await _read_upload_csv(file, "market")
    return {"status": "market uploaded", "rows": len(market_df_cache)}


async def _upload_research_file(file: UploadFile):
    global research_df_cache
    research_df_cache = await _read_upload_csv(file, "research")
    return {"status": "research uploaded", "rows": len(research_df_cache)}


@app.post("/research/upload")
async def upload_research(file: UploadFile = File(...)):
    return await _upload_research_file(file)


@app.post("/equity-reports/upload")
async def upload_equity_reports(file: UploadFile = File(...)):
    return await _upload_research_file(file)


@app.post("/recommendation")
async def recommend(request: Request):
    global market_df_cache, research_df_cache

    content_type = request.headers.get("content-type", "")
    market_df = market_df_cache
    research_df = research_df_cache

    if "multipart/form-data" in content_type:
        form = await request.form()
        profile_raw = form.get("profile")
        profile_data = json.loads(profile_raw) if isinstance(profile_raw, str) else {}

        market_file = form.get("market_file")
        if isinstance(market_file, UploadFile):
            market_df = await _read_upload_csv(market_file, "market")

        research_file = form.get("research_file")
        if isinstance(research_file, UploadFile):
            research_df = await _read_upload_csv(research_file, "research")
    else:
        profile_data = await request.json()

    if market_df is None:
        raise HTTPException(status_code=400, detail="No market data uploaded")

    profile = InvestorProfile(**profile_data)
    return _recommend_from_data(market_df, research_df, profile)


@app.get("/reset")
def reset():
    global market_df_cache, research_df_cache
    market_df_cache = None
    research_df_cache = None
    return {"message": "reset done"}


@app.get("/{full_path:path}")
def serve_frontend(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")

    requested_file = FRONTEND_BUILD_DIR / full_path
    index_file = FRONTEND_BUILD_DIR / "index.html"

    if requested_file.is_file():
        return FileResponse(requested_file)

    if index_file.is_file():
        return FileResponse(index_file, media_type="text/html")

    raise HTTPException(status_code=404, detail="Frontend build not found.")
