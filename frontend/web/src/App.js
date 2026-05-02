import React, { useEffect, useState } from "react";
import "./App.css";
import { getApiStatus, getRecommendation, uploadCsv } from "./api";

const initialProfile = {
  age: 25,
  income: 100000,
  investment_amount: 20000,
  risk_preference: "Medium",
  financial_goals: "Wealth growth",
  time_period_years: 5,
};

function App() {
  const [form, setForm] = useState(initialProfile);
  const [portfolio, setPortfolio] = useState(null);
  const [methodology, setMethodology] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("Checking API");
  const [message, setMessage] = useState("");

  useEffect(() => {
    getApiStatus()
      .then((data) => setStatus(data.status || "API connected"))
      .catch(() => setStatus("API offline"));
  }, []);

  const handleChange = (e) => {
    const { name, value, type } = e.target;
    setForm({
      ...form,
      [name]: type === "number" ? Number(value) : value,
    });
  };

  const uploadFile = async (file, endpoint, label) => {
    if (!file) return;

    setMessage(`Uploading ${label}...`);

    try {
      const data = await uploadCsv(file, endpoint);
      setMessage(`${label} uploaded: ${data.rows} rows`);
    } catch (err) {
      setMessage(err.message);
    }
  };

  const handleRecommendation = async () => {
    setLoading(true);
    setMessage("");

    try {
      const data = await getRecommendation(form);
      setPortfolio(data.portfolio || []);
      setMethodology(data.methodology || "");
      setMessage("Recommendation ready");
    } catch (err) {
      setPortfolio(null);
      setMethodology("");
      setMessage(err.message || "Backend not responding");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="dashboard">
      <section className="hero">
        <div>
          <p className="eyebrow">Portfolio intelligence</p>
          <h1>AI Investment Portfolio Advisor</h1>
          <p className="subtitle">
            A clean risk-return dashboard for PSX market data, research scores, and investor profile based recommendations.
          </p>
        </div>
        <div className="status-pill">{status}</div>
      </section>

      <section className="grid uploads">
        <div className="panel">
          <span className="panel-label">Market CSV</span>
          <h2>Market Data</h2>
          <input type="file" accept=".csv" onChange={(e) => uploadFile(e.target.files[0], "market/upload", "Market data")} />
        </div>

        <div className="panel">
          <span className="panel-label">Research CSV</span>
          <h2>Equity Research</h2>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => uploadFile(e.target.files[0], "equity-reports/upload", "Research data")}
          />
        </div>
      </section>

      <section className="panel profile-panel">
        <div className="section-heading">
          <span className="panel-label">Investor profile</span>
          <h2>Recommendation Inputs</h2>
        </div>

        <div className="form-grid">
          <label>
            Age
            <input name="age" type="number" value={form.age} onChange={handleChange} />
          </label>
          <label>
            Income
            <input name="income" type="number" value={form.income} onChange={handleChange} />
          </label>
          <label>
            Investment Amount
            <input name="investment_amount" type="number" value={form.investment_amount} onChange={handleChange} />
          </label>
          <label>
            Risk Preference
            <select name="risk_preference" value={form.risk_preference} onChange={handleChange}>
              <option>Low</option>
              <option>Medium</option>
              <option>High</option>
            </select>
          </label>
          <label>
            Financial Goals
            <input name="financial_goals" value={form.financial_goals} onChange={handleChange} />
          </label>
          <label>
            Time Period
            <input name="time_period_years" type="number" value={form.time_period_years} onChange={handleChange} />
          </label>
        </div>

        <div className="actions">
          <button onClick={handleRecommendation} className="btn" disabled={loading}>
            {loading ? "Processing..." : "Get Recommendation"}
          </button>
          {message && <p className="message">{message}</p>}
        </div>
      </section>

      {portfolio && (
        <section className="panel results-panel">
          <div className="section-heading">
            <span className="panel-label">Optimized output</span>
            <h2>Recommended Portfolio</h2>
          </div>
          {methodology && <p className="methodology">{methodology}</p>}

          <div className="portfolio-grid">
            {portfolio.map((item) => (
              <article key={item.symbol} className="stock-card">
                <div className="stock-header">
                  <div>
                    <h3>{item.symbol}</h3>
                    {item.sector && <span className="sector">{item.sector}</span>}
                  </div>
                  <strong>{item.allocation_pct}%</strong>
                </div>

                <div className="bar" aria-label={`${item.symbol} allocation`}>
                  <div style={{ width: `${Math.min(item.allocation_pct, 100)}%` }} className="fill" />
                </div>

                <p>Score: {item.score}</p>
                <small>{item.reasons.join(" | ")}</small>
              </article>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}

export default App;
