const defaultBaseUrl =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://web-production-fd1ce.up.railway.app";

const BASE_URL = (process.env.REACT_APP_API_BASE || defaultBaseUrl).replace(/\/$/, "");

const parseResponse = async (res) => {
  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.detail || data.error || "Request failed");
  }

  return data;
};

export const uploadCsv = async (file, endpoint) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/${endpoint}`, {
    method: "POST",
    body: formData,
  });

  return parseResponse(res);
};

export const getRecommendation = async (profile) => {
  const res = await fetch(`${BASE_URL}/recommendation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });

  return parseResponse(res);
};

export const getApiStatus = async () => {
  const res = await fetch(`${BASE_URL}/api/health`);
  return parseResponse(res);
};
