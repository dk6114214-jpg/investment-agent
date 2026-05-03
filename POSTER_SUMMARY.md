# 📊 AI Investment Portfolio Advisor
## Smart Risk-Return Optimization for PSX

---

## ✨ What It Does

Transform your **investment data** into **optimized portfolio recommendations** using **Markowitz Modern Portfolio Theory**.

### Three Simple Steps:
1. **Upload** PSX market data (CSV)
2. **Enter** your investment profile (age, income, risk preference)
3. **Get** AI-recommended portfolio with risk scores

---

## 🎯 Core Technology

### Mathematical Framework: Modern Portfolio Theory
```
SHARPE RATIO = Expected Return ÷ Volatility

Higher Sharpe = Better Risk-Adjusted Returns
```

### Scoring Formula:
```
PORTFOLIO SCORE =
  ✓ Return Score (35%)
  ✓ Risk Score (25%)
  ✓ Sharpe Ratio (20%)  ← Risk-Adjusted Excellence
  ✓ Fundamental Score (10%)
  ✓ Confidence Score (6%)
  ✓ Liquidity Score (4%)
```

---

## 📈 Key Features

| Feature | Description |
|---------|-------------|
| **Data-Driven** | Uses ONLY uploaded CSVs, no stored data |
| **Risk-Adjusted** | Sharpe ratio weighing for optimal balance |
| **Personalized** | Adjusts for your age, income, risk preference |
| **Diversified** | Selects top 5 stocks across sectors |
| **Transparent** | Shows all metrics: returns, volatility, scores |

---

## 🔢 What You Get

### For Each Stock:
```
SYMBOL: MCB
Sector: Banking
Allocation: 23.98%

Returns: 18.5% annually
Risk: 22.3% volatility  
Sharpe Ratio: 0.83

Fundamental Quality: 85.2/100
Analyst Confidence: 88.5/100
Liquidity: 92.1/100
```

### Overall Portfolio:
✓ Total allocation = 100% (diversified)
✓ Risk-adjusted for your preference
✓ Methodology explanation included

---

## 💼 Risk Preferences

### LOW RISK
- Max allocation per stock: 28%
- Conservative returns with stability

### MEDIUM RISK  
- Max allocation per stock: 34%
- Balanced growth and safety

### HIGH RISK
- Max allocation per stock: 42%
- Aggressive returns, higher volatility

---

## 🚀 Technical Stack

**Backend**: FastAPI (Python)
**Frontend**: React 19
**Theory**: Markowitz Modern Portfolio Theory
**Optimization**: NumPy, Pandas
**Deployment**: Railway

---

## 📁 Input Data Format

### Market CSV
```
symbol,price,volume,sector
MCB,350.50,5000000,Banking
HBL,125.75,8000000,Banking
ENGRO,185.25,2000000,Energy
```

### Research CSV (Optional)
```
symbol,FA Score,Confidence
MCB,0.92,0.89
HBL,0.78,0.81
```

---

## ✅ Why It Works

1. **Markowitz Theory**: Proven mathematical approach since 1952
2. **Sharpe Focus**: 20% weight on risk-adjusted returns
3. **Real Data**: Processes actual PSX market data you provide
4. **Adaptive**: Changes recommendations based on your profile
5. **Transparent**: Shows all calculations and reasoning

---

## 🎓 The Math Behind It

### Expected Return Estimation
```
Return = 4% Base
       + 14% × Fundamental Quality
       + 5% × Analyst Confidence  
       + 3% × Price Factor
       
Range: 3% to 32% annually
```

### Risk (Volatility) Estimation
```
Risk = 28% Base
     - 10% × Fundamental Quality
     - 5% × Analyst Confidence
     + 10% × Liquidity Risk
     
Range: 6% to 40% annually
```

### The Key Metric
```
SHARPE RATIO = Return ÷ Risk

This balances:
  ✓ How much return you could get
  ✓ How much risk you take
  ✓ Whether the return justifies the risk
```

---

## 🌐 System Access

**Local**: http://127.0.0.1:3001
**Production**: [Deployed on Railway]

### How to Use:
1. Select **psx_market.csv** (required)
2. Select **psx_research.csv** (optional)
3. Adjust investor profile if needed
4. Click "Get Recommendation"
5. View optimized portfolio with all metrics

---

## 🔐 Data Privacy

✓ **Stateless**: No data stored between requests
✓ **Fresh**: Each recommendation uses uploaded files only
✓ **Secure**: CORS protected API
✓ **Transparent**: All formulas visible in code

---

## 📊 Sample Output

```
RECOMMENDED PORTFOLIO
Risk Preference: HIGH
Investment Amount: PKR 20,000

1. MCB (Banking)        23.98% | Return: 18.5% | Risk: 22.3% | Sharpe: 0.83
2. LUCK (Diversified)   25.30% | Return: 17.2% | Risk: 20.8% | Sharpe: 0.83
3. ENGRO (Energy)       18.73% | Return: 16.8% | Risk: 19.5% | Sharpe: 0.86
4. OGDC (Energy)        16.60% | Return: 16.1% | Risk: 18.9% | Sharpe: 0.85
5. HBL (Banking)        15.39% | Return: 15.4% | Risk: 18.2% | Sharpe: 0.85

TOTAL: 100% allocation
Expected Portfolio Return: ~17.5%
Expected Portfolio Risk: ~20.3%
Portfolio Sharpe Ratio: 0.86
```

---

## 🎯 Why Choose This Advisor?

| Traditional | Our AI Advisor |
|------------|-----------------|
| Manual stock picks | Data-driven recommendations |
| Gut feeling | Mathematical optimization |
| Single focus | Risk-return balanced |
| No transparency | All metrics shown |
| Static | Adapts to your profile |

---

## 📞 Contact & Support

For questions about:
- **How it works**: See Technical Documentation
- **Data format**: Check sample CSVs
- **Theory**: Review Markowitz Modern Portfolio Theory

---

**Version**: 1.0.0  
**Last Updated**: May 3, 2026  
**Status**: ✅ Production Ready

*Empowering Smart Investments Through Data & Mathematics*
