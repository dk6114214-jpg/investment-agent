# AI Investment Portfolio Advisor - Technical Documentation

## System Architecture

### Backend (FastAPI Python)
- **Port**: 8002
- **Framework**: FastAPI 0.136.1
- **Database**: Stateless (no persistent storage)
- **Data Processing**: Pandas, NumPy

### Frontend (React)
- **Port**: 3001
- **Framework**: React 19.2.4
- **Build Tool**: react-scripts 5.0.1
- **Communication**: REST API via fetch

---

## Data Flow

### User Inputs
1. **Investor Profile**:
   - Age (years)
   - Annual Income (PKR)
   - Investment Amount (PKR)
   - Risk Preference (Low/Medium/High)
   - Financial Goals (text)
   - Investment Horizon (years)

2. **File Uploads** (CSV format):
   - **Market CSV**: Symbol, Price, Volume, Sector
   - **Research CSV** (optional): Symbol, FA Score, Confidence Score

### Processing Pipeline
```
Uploaded CSVs → Parse & Validate → Compute Metrics → Optimize Weights → Rank Portfolio
```

---

## Mathematical Framework

### Modern Portfolio Theory (Markowitz)

#### Step 1: Estimate Expected Return
```
Expected Return = 4% + (Fundamental Score × 14%) + (Confidence × 5%) + (Price Score × 3%)
Range: 3% to 32% annually
```

#### Step 2: Estimate Volatility (Risk)
```
Volatility = 28% - (Fundamental × 10%) - (Confidence × 5%) + (Illiquidity Risk × 10%)
Range: 6% to 40% annually
```

#### Step 3: Calculate Sharpe Ratio (Risk-Adjusted Return)
```
Sharpe Ratio = Expected Return / Volatility

This is the CORE of Markowitz theory:
- Higher Sharpe = Better risk-adjusted returns
- Balances return potential with downside risk
```

#### Step 4: Composite Score
```
Risk-Adjusted Score = 
  (Return Score × 35%)
  + (Risk Score × 25%)
  + (Sharpe Ratio Score × 20%)    ← Risk adjustment
  + (Fundamental Score × 10%)
  + (Confidence Score × 6%)
  + (Liquidity Score × 4%)
```

---

## Portfolio Selection

### Algorithm
1. Score all available assets using composite formula
2. Rank by risk-adjusted score (highest first)
3. Select top 5 assets
4. Optimize weights using constrained mean-variance approach

### Weight Constraints (by Risk Preference)
- **Low Risk**: Max weight = 28% per asset
- **Medium Risk**: Max weight = 34% per asset  
- **High Risk**: Max weight = 42% per asset

### Weight Normalization
```
Weights are re-scaled to sum to 100% while respecting max constraints
```

---

## Key Metrics in Output

### For Each Stock:
- **Symbol**: Company ticker
- **Sector**: Industry classification
- **Allocation %**: Portfolio weight (sums to 100%)
- **Expected Return**: Annual return forecast (%)
- **Volatility**: Annual risk/standard deviation (%)
- **Sharpe Ratio**: Risk-adjusted efficiency score
- **Fundamental Score**: Research-based quality (0-100)
- **Confidence Score**: Analyst conviction (0-100)
- **Liquidity Score**: Trading volume efficiency (0-100)

### Portfolio Methodology
- **Advanced risk-adjusted portfolio** using Sharpe ratio
- **Sector diversification** considered
- **Data-driven allocation** based on uploaded files
- **Investor profile** adjusts allocations for optimal balance

---

## API Endpoints

### Health Check
```
GET /api/health
Response: {"status": "running", "data_loaded": true}
```

### Get Recommendation
```
POST /recommendation
Content-Type: multipart/form-data

Parameters:
- market_file (CSV): Required
- research_file (CSV): Optional
- profile (JSON): Investor profile

Response: {
  "model": "DATA_DRIVEN_PORTFOLIO_V1",
  "risk_preference": "Medium",
  "investment_amount": 20000,
  "portfolio": [
    {
      "symbol": "MCB",
      "sector": "Banking",
      "allocation_pct": 23.98,
      "score": 66.91,
      "expected_return": 18.5,
      "volatility": 22.3,
      "sharpe_ratio": 0.83,
      "fundamental_score": 85.2,
      "liquidity_score": 92.1,
      "confidence_score": 88.5,
      "reasons": [...]
    }
  ],
  "methodology": "..."
}
```

---

## Data Characteristics

### CSV File Format

**market_upload_sample.csv**:
```
symbol,price,volume,sector
MCB,350.50,5000000,Banking
HBL,125.75,8000000,Banking
ENGRO,185.25,2000000,Energy
LUCK,42.10,1500000,Diversified
OGDC,95.50,3000000,Energy
```

**equity_reports_upload_sample.csv**:
```
symbol,FA Score,Confidence
MCB,0.92,0.89
HBL,0.78,0.81
ENGRO,0.85,0.76
LUCK,0.65,0.72
OGDC,0.88,0.85
```

---

## Risk Management

### Price Normalization
- All prices normalized to 0-1 range
- Extreme values clipped to prevent outliers

### Score Constraints
- Expected return clamped to 3% - 32%
- Volatility clamped to 6% - 40%
- All component scores normalized to 0-100

### Weight Constraints
- No single asset exceeds max weight based on risk preference
- Weights always sum to 100%

---

## Deployment

### Local Testing
```
Backend:  http://127.0.0.1:8002
Frontend: http://127.0.0.1:3001
```

### Production (Railway)
- Uvicorn serves backend
- React build serves frontend as static files
- CORS enabled for cross-origin requests

---

## Key Advantages

✅ **Markowitz-based**: Uses modern portfolio theory for optimal risk-return tradeoff
✅ **Sharpe Ratio Focus**: 20% weight on risk-adjusted returns
✅ **Data-Driven**: No stored data; uses uploaded files only
✅ **Investor-Centric**: Adapts allocations based on risk preference
✅ **Sector Diversification**: Considers industry classification
✅ **Transparent Scoring**: Shows all component metrics

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend API | FastAPI | 0.136.1 |
| Web Framework | Python | 3.11+ |
| Data Processing | Pandas | 2.0+ |
| Numerical | NumPy | 1.24+ |
| Frontend | React | 19.2.4 |
| Frontend Build | react-scripts | 5.0.1 |
| Deployment | Uvicorn | 0.27+ |
| CORS | fastapi.middleware | Built-in |

---

## File Locations

```
backend/
  api/
    main.py           ← Core API endpoints
    ml_model.py       ← Data processing
    engine optimizer.py ← Weight optimization
  data_pipeline/
    psx_market.csv    ← Sample market data
    psx_research.csv  ← Sample research data

frontend/
  web/
    src/
      App.js          ← Main React component
      api.js          ← API client
```

---

**Last Updated**: May 3, 2026
**Version**: 1.0.0
**Author**: AI Investment Portfolio Team
