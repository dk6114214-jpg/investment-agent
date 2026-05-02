const defaultBaseUrl =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://web-production-fd1ce.up.railway.app";

const BASE_URL = (
  process.env.REACT_APP_API_BASE || defaultBaseUrl
).replace(/\/$/, "");

// --------------------
// Helper: Parse response
// --------------------
const parseResponse = async (res) => {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }

  return data;
};

// --------------------
// Upload CSV (Market / Research)
// --------------------
export const uploadCsv = async (file, endpoint) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/${endpoint}`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(res);
};

// --------------------
// Get Recommendation (MAIN FIX SAFE)
// --------------------
export const getRecommendation = async (profile) => {
  const res = await fetch(`${BASE_URL}/recommendation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      age: profile.age,
      income: profile.income,
      investment_amount: profile.investmentAmount,
      risk_preference: profile.riskPreference,
      financial_goals: profile.financialGoals,
      time_period_years: profile.timePeriod,
    }),
  });

  return parseResponse(res);
};

// --------------------
// API Status (FIXED - NO /api/health)
// --------------------
export const getApiStatus = async () => {
  try {
    const res = await fetch(`${BASE_URL}/`);
    return await res.json();
  } catch (err) {
    console.error("API health check failed:", err);
    throw err;
  }
};