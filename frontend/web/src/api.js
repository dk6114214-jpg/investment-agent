const BASE_URL =
  process.env.REACT_APP_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

// ---------- STATUS ----------
export const getApiStatus = async () => {
  try {
    const res = await fetch(`${BASE_URL}/`);
    if (!res.ok) throw new Error("API offline");
    return await res.json();
  } catch (e) {
    return { status: "API offline" };
  }
};

const readError = async (res, fallback) => {
  const err = await res.json().catch(() => ({}));
  return err.detail || err.error || fallback;
};

// ---------- UPLOAD CSV ----------
export const uploadCsv = async (file, endpoint) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/${endpoint}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(await readError(res, "Upload failed"));
  }

  return res.json();
};

export const uploadMarketCsv = (file) => uploadCsv(file, "market/upload");

export const uploadResearchCsv = async (file) => {
  try {
    return await uploadCsv(file, "equity-reports/upload");
  } catch (err) {
    if (err.message !== "Not Found") {
      throw err;
    }
    return uploadCsv(file, "research/upload");
  }
};

// ---------- RECOMMENDATION ----------
export const getRecommendation = async (profile) => {
  const res = await fetch(`${BASE_URL}/recommendation`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(profile),
  });

  if (!res.ok) {
    throw new Error(await readError(res, "Recommendation failed"));
  }

  return res.json();
};
