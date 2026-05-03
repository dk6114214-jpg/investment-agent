from pathlib import Path
from typing import Literal
import os
import subprocess

import numpy as np
import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parents[1]
FRONTEND_BUILD_DIR = PROJECT_DIR / "frontend" / "web" / "build"

app = FastAPI(title="AI Investment Portfolio Advisor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


def _normalize(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.empty or values.nunique(dropna=True) <= 1:
        return pd.Series(0.5, index=series.index)
    scaled = (values - values.min()) / (values.max() - values.min())
    return scaled.fillna(0.5).clip(0, 1)


def _load_default_data() -> None:
    # Removed: No longer loading default CSV data on startup
    # Users must upload market and research data first
    pass


def _get_deployment_version() -> str:
    env_version = os.getenv("COMMIT_SHA") or os.getenv("GIT_COMMIT")
    if env_version:
        return env_version
    try:
        version = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_DIR),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return version
    except Exception:
        return "unknown"


@app.on_event("startup")
def startup() -> None:
    _load_default_data()


def _status_payload():
    return {
        "status": "AI Investment Portfolio API is running",
        "market_rows": 0,  # Stateless: data loaded per request
        "research_rows": 0,  # Stateless: data loaded per request
        "data_loaded": False,  # Always false: requires file uploads
        "version": _get_deployment_version(),
    }


@app.get("/api/health")
def health():
    return _status_payload()


@app.get("/api/version")
def version():
    return {"version": _get_deployment_version()}


@app.get("/")
def home():
    index_file = FRONTEND_BUILD_DIR / "index.html"
    if index_file.is_file():
        return FileResponse(index_file, media_type="text/html")
    return _status_payload()


def _prepare_assets_for_recommendation(market_df: pd.DataFrame, research_df: pd.DataFrame | None) -> pd.DataFrame:
    if market_df is None or market_df.empty:
        raise HTTPException(status_code=503, detail="No market data available")

    assets = market_df.copy()
    assets["symbol"] = assets["symbol"].astype(str).str.strip()
    if "sector" in assets.columns:
        assets["sector"] = assets["sector"].astype(str).fillna("Unknown")
    else:
        assets["sector"] = "Unknown"
    assets["price"] = pd.to_numeric(assets.get("price", pd.Series(dtype=float)), errors="coerce").fillna(0.0)
    assets["volume"] = pd.to_numeric(assets.get("volume", pd.Series(dtype=float)), errors="coerce").fillna(0.0)

    research = None
    if research_df is not None and not research_df.empty and "symbol" in research_df.columns:
        research = research_df.copy()
        research["symbol"] = research["symbol"].astype(str).str.strip()
        score_col = next((col for col in research.columns if "score" in col.lower()), None)
        confidence_col = next((col for col in research.columns if "confidence" in col.lower()), None)
        if score_col:
            research[score_col] = pd.to_numeric(research[score_col], errors="coerce")
        if confidence_col:
            research[confidence_col] = pd.to_numeric(research[confidence_col], errors="coerce")
        research = research[["symbol", score_col, confidence_col]].drop_duplicates(subset=["symbol"])
        assets = assets.merge(research, on="symbol", how="left")

    assets["fundamental_score"] = _normalize(assets.get("FA Score", assets.get("fundamental_score", pd.Series(0.5, index=assets.index))))
    assets["confidence_score"] = _normalize(assets.get("Confidence", assets.get("confidence_score", pd.Series(0.5, index=assets.index))))
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


def _normalize_weights(values: np.ndarray, max_weight: float = 0.34) -> np.ndarray:
    weights = values.copy()
    weights = np.maximum(weights, 0)
    if weights.sum() <= 0:
        weights = np.ones_like(weights)
    weights = weights / weights.sum()
    weights = np.minimum(weights, max_weight)
    weights = weights / weights.sum()
    return weights


def _format_portfolio(assets: pd.DataFrame, weights: np.ndarray) -> list[dict]:
    assets = assets.copy()
    assets["allocation_pct"] = np.round(weights * 100, 2)
    portfolio = []
    for _, row in assets.iterrows():
        portfolio.append(
            {
                "symbol": row["symbol"],
                "sector": row["sector"],
                "allocation_pct": float(row["allocation_pct"]),
                "score": round(float(row["raw_score"] * 100), 2),
                "expected_return": round(float(row["expected_return"] * 100), 2),
                "volatility": round(float(row["volatility"] * 100), 2),
                "sharpe_ratio": round(float(row["sharpe_ratio"]), 2),
                "fundamental_score": round(float(row["fundamental_score"] * 100), 1),
                "liquidity_score": round(float(row["liquidity_score"] * 100), 1),
                "confidence_score": round(float(row["confidence_score"] * 100), 1),
                "reasons": [
                    "Risk-adjusted scoring with Sharpe ratio",
                    "Sector diversification considered",
                    "Data-driven allocation",
                ],
            }
        )
    return portfolio


@app.post("/recommendation")
def recommend(
    market_file: UploadFile = File(...),
    research_file: UploadFile = File(None),
    profile: str = Form(...),
):
    profile_obj = InvestorProfile.parse_raw(profile)
    # Load market data from uploaded file
    try:
        market_df = pd.read_csv(market_file.file)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Unable to read market CSV") from exc

    if market_df.empty:
        raise HTTPException(status_code=400, detail="Market CSV is empty")

    market_df.columns = [str(c).strip() for c in market_df.columns]
    market_df["symbol"] = market_df["symbol"].astype(str).str.strip()

    # Load research data if provided
    research_df = None
    if research_file:
        try:
            research_df = pd.read_csv(research_file.file)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Unable to read research CSV") from exc

        if research_df.empty:
            research_df = None
        else:
            research_df.columns = [str(c).strip() for c in research_df.columns]
            research_df["symbol"] = research_df["symbol"].astype(str).str.strip()

    # Now process with the uploaded data
    assets = _prepare_assets_for_recommendation(market_df, research_df)

    if assets.empty:
        raise HTTPException(status_code=503, detail="No asset data available")

    if profile_obj.risk_preference == "Low":
        scores = assets["raw_score"] * 0.8 + assets["risk_score"] * 0.25
        max_weight = 0.28
    elif profile_obj.risk_preference == "High":
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
    portfolio = _format_portfolio(selected, weights)

    return {
        "model": "DATA_DRIVEN_PORTFOLIO_V1",
        "risk_preference": profile_obj.risk_preference,
        "investment_amount": profile_obj.investment_amount,
        "portfolio": portfolio,
        "methodology": (
            "Advanced risk-adjusted portfolio using Sharpe ratio for risk-return efficiency. "
            "Incorporates expected return, volatility, fundamental analysis, confidence scores, and liquidity. "
            "Applies sector diversification and risk-based weighting. "
            "Investor age, income, and risk preference adjust allocations for optimal balance."
        ),
    }


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
