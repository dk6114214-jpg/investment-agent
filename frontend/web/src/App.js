import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import {
  getApiStatus,
  getRecommendation,
  uploadMarketCsv,
  uploadResearchCsv,
} from "./api";

const initialProfile = {
  age: 25,
  income: 100000,
  investment_amount: 20000,
  risk_preference: "Medium",
  financial_goals: "Wealth growth",
  time_period_years: 5,
};

const featureCards = [
  ["CSV Market Analysis", "Upload PSX market and research CSV files for structured analysis."],
  ["Investor Profiling", "Age, income, investment amount, risk profile, goal, and horizon shape the output."],
  ["Risk Return Optimization", "Expected return, volatility, liquidity, and confidence drive ranking."],
  ["AI Ranking Engine", "Random Forest inspired scoring ranks stocks before allocation is generated."],
];

const modelCards = [
  ["Problem", "Retail PSX investors lack data-driven tools, struggle with risk-return balance, and rely on scattered research."],
  ["Solution", "The system analyzes uploaded data and investor profile to generate optimized recommendations."],
  ["Mathematical Model", "Sharpe Ratio = (R_p - R_f) / sigma_p, with objective to improve portfolio weights."],
  ["Tech Stack", "React dashboard, FastAPI backend, Pandas and NumPy processing, Scikit-Learn ML engine."],
];

const getStockAmount = (stock, investmentAmount) => {
  const directAmount = Number(stock.amount);
  if (Number.isFinite(directAmount)) {
    return directAmount;
  }

  const allocation = Number(stock.allocation_pct || stock.allocation || 0);
  return Number(investmentAmount || 0) * (allocation / 100);
};

const getMetricFromReasons = (stock, label) => {
  const reason = (stock.reasons || []).find((item) =>
    String(item).toLowerCase().startsWith(label.toLowerCase())
  );
  return reason ? reason.split(":").slice(1).join(":").trim() : "--";
};

function App() {
  const [form, setForm] = useState(initialProfile);
  const [portfolio, setPortfolio] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [methodology, setMethodology] = useState("");
  const [status, setStatus] = useState("Checking API...");
  const [message, setMessage] = useState("Upload market CSV to begin.");
  const [loading, setLoading] = useState(false);
  const [marketFile, setMarketFile] = useState(null);
  const [researchFile, setResearchFile] = useState(null);

  useEffect(() => {
    getApiStatus()
      .then((res) => {
        setStatus(res.status || "API connected");
        setMessage("Upload market CSV to begin.");
      })
      .catch(() => setStatus("API offline"));
  }, []);

  const totals = useMemo(() => {
    const topScore = portfolio.reduce((max, stock) => Math.max(max, Number(stock.score || 0)), 0);
    return {
      amount: Number(form.investment_amount || 0),
      topScore,
      count: portfolio.length,
    };
  }, [portfolio, form.investment_amount]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numeric = ["age", "income", "investment_amount", "time_period_years"];
    setForm((prev) => ({
      ...prev,
      [name]: numeric.includes(name) ? Number(value) : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!marketFile) {
      setMessage("Please upload the market CSV first.");
      return;
    }

    setLoading(true);
    setMessage("Uploading CSV data...");

    try {
      await uploadMarketCsv(marketFile);
      if (researchFile) {
        await uploadResearchCsv(researchFile);
      }

      setMessage("Generating optimized portfolio...");
      const res = await getRecommendation(form);
      const resultPortfolio = res.portfolio || [];

      setPortfolio(resultPortfolio);
      setMetrics(
        res.metrics || {
          total_symbols: resultPortfolio.length,
          recommended_symbols: resultPortfolio.length,
          research_coverage: researchFile ? "Uploaded" : "--",
          average_score: resultPortfolio.length
            ? (
                resultPortfolio.reduce((sum, stock) => sum + Number(stock.score || 0), 0) /
                resultPortfolio.length
              ).toFixed(2)
            : "--",
        }
      );
      setMethodology(res.methodology || "");
      setMessage("Recommendation ready.");
    } catch (err) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#agent" aria-label="PSX Portfolio Optimizer dashboard">
          <span>PO</span>
          <strong>PSX Portfolio Optimizer</strong>
          <small>v2.0</small>
        </a>
        <nav>
          <a href="#about">Problem</a>
          <a href="#features">Features</a>
          <a href="#model">Model</a>
          <a href="#output">Output</a>
          <a className="launch-link" href="#agent">Launch Agent</a>
        </nav>
      </header>

      <main>
        <section className="hero" id="agent">
          <div className="hero-copy">
            <span className="eyebrow">Smart portfolio recommendations for PSX investors</span>
            <h1>
              AI-Driven <span>Portfolio Optimization</span>
            </h1>
            <p>
              Upload market and research data, enter the investor profile, and
              generate a risk-aware portfolio with allocation percentages,
              ranking scores, and clear explanations.
            </p>
            <div className="hero-actions">
              <a className="btn" href="#dashboard">Launch Agent</a>
              <a className="btn ghost" href="#model">View Model</a>
            </div>
          </div>

          <form className="agent-panel" id="dashboard" onSubmit={handleSubmit}>
            <div className="panel-heading">
              <span className="panel-label">Live Recommendation Engine</span>
              <span className="status-pill">{status}</span>
            </div>

            <div className="upload-grid">
              <label>
                Market CSV
                <input type="file" accept=".csv" onChange={(e) => setMarketFile(e.target.files[0] || null)} />
              </label>
              <label>
                Research CSV
                <input type="file" accept=".csv" onChange={(e) => setResearchFile(e.target.files[0] || null)} />
              </label>
            </div>

            <div className="form-grid">
              <label>
                Age
                <input name="age" type="number" min="18" value={form.age} onChange={handleChange} />
              </label>
              <label>
                Monthly Income
                <input name="income" type="number" min="0" value={form.income} onChange={handleChange} />
              </label>
              <label>
                Investment Amount
                <input name="investment_amount" type="number" min="1000" value={form.investment_amount} onChange={handleChange} />
              </label>
              <label>
                Risk Profile
                <select name="risk_preference" value={form.risk_preference} onChange={handleChange}>
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                </select>
              </label>
              <label>
                Goal
                <input name="financial_goals" value={form.financial_goals} onChange={handleChange} />
              </label>
              <label>
                Time Period
                <input name="time_period_years" type="number" min="1" value={form.time_period_years} onChange={handleChange} />
              </label>
            </div>

            <div className="actions">
              <button className="btn" type="submit" disabled={loading}>
                {loading ? "Processing..." : "Get Recommendation"}
              </button>
              <p className="message">{message}</p>
            </div>
          </form>
        </section>

        <section className="stats-band" aria-label="Dashboard metrics">
          <article>
            <span>Total Capital</span>
            <strong>PKR {Math.round(totals.amount).toLocaleString()}</strong>
          </article>
          <article>
            <span>Recommendations</span>
            <strong>{totals.count}</strong>
          </article>
          <article>
            <span>Top Score</span>
            <strong>{totals.topScore || "--"}</strong>
          </article>
          <article>
            <span>Research Data</span>
            <strong>{metrics ? metrics.research_coverage : "--"}</strong>
          </article>
        </section>

        <section className="results-section">
          <div className="section-heading">
            <span className="eyebrow">Portfolio Output</span>
            <h2>Optimized Allocation</h2>
            {methodology && <p>{methodology}</p>}
          </div>

          <div className="portfolio-grid">
            {portfolio.length === 0 ? (
              <div className="empty-state">
                <strong>No recommendation yet</strong>
                <p>Upload market and research CSV files, then run the recommendation engine.</p>
              </div>
            ) : (
              portfolio.map((stock) => (
                <article className="stock-card" key={stock.symbol}>
                  <div className="stock-header">
                    <div>
                      <h3>{stock.symbol}</h3>
                      <span>{stock.company_name && stock.company_name !== stock.symbol ? stock.company_name : "PSX Equity"}</span>
                    </div>
                    <strong>{stock.allocation_pct}%</strong>
                  </div>
                  <div className="bar" aria-hidden="true">
                    <span style={{ width: `${Math.min(Number(stock.allocation_pct || 0), 100)}%` }} />
                  </div>
                  <div className="stock-meta">
                    <span>{stock.sector || "Sector"}</span>
                    <span>Ranked</span>
                    <span>Score {stock.score}</span>
                  </div>
                  <p>
                    PKR {Math.round(getStockAmount(stock, form.investment_amount)).toLocaleString()} suggested allocation
                  </p>
                  <small>{(stock.reasons || []).join(" | ")}</small>
                </article>
              ))
            )}
          </div>
        </section>

        {portfolio.length > 0 && (
          <section className="output-table" id="output">
            <div className="section-heading">
              <span className="eyebrow">Table Data</span>
              <h2>Stock, Allocation, Return, Risk, Score, Rank</h2>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Rank</th>
                    <th>Stock</th>
                    <th>Allocation</th>
                    <th>Exp. Return</th>
                    <th>Risk</th>
                    <th>Score</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.map((stock, index) => (
                    <tr key={stock.symbol}>
                      <td>{index + 1}</td>
                      <td>{stock.symbol}</td>
                      <td>{stock.allocation_pct}%</td>
                      <td>{getMetricFromReasons(stock, "Expected return")}</td>
                      <td>{getMetricFromReasons(stock, "Volatility estimate")}</td>
                      <td>{stock.score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        <section className="content-section" id="about">
          <span className="eyebrow">Problem + Solution</span>
          <h2>Data-Driven Decisions for Retail PSX Investors</h2>
          <p>
            Retail investors often lack decision tools, struggle to balance risk
            and return, and depend on guesswork. The optimizer analyzes uploaded
            market and research data, understands investor profile, and generates
            optimized portfolio recommendations.
          </p>
        </section>

        <section className="feature-grid" id="features">
          {featureCards.map(([title, text]) => (
            <article key={title}>
              <h3>{title}</h3>
              <p>{text}</p>
            </article>
          ))}
        </section>

        <section className="model-grid" id="model">
          {modelCards.map(([title, text]) => (
            <article key={title}>
              <span className="eyebrow">{title}</span>
              <p>{text}</p>
            </article>
          ))}
        </section>
      </main>

      <footer>PSX Portfolio Optimizer | React Dashboard | FastAPI | Pandas | NumPy | Scikit-Learn</footer>
    </div>
  );
}

export default App;
