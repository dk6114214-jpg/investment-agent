const BASE_URL = process.env.REACT_APP_API_BASE || "";

const makeUrl = (path) => {
  const normalizedPath = path.startsWith("/") ? path.slice(1) : path;
  if (!BASE_URL) {
    return `/${normalizedPath}`;
  }
  const prefix = BASE_URL.endsWith("/") ? "" : "/";
  return `${BASE_URL}${prefix}${normalizedPath}`;
};

// -----------------------
// UPLOAD CSV
// -----------------------
export const uploadCsv = async (file, endpoint) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(makeUrl(endpoint), {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload CSV");
  }

  return await res.json();
};

// -----------------------
// GET RECOMMENDATION
// -----------------------
export const getRecommendation = async (marketFile, researchFile, profile) => {
  const formData = new FormData();
  formData.append("market_file", marketFile);
  if (researchFile) {
    formData.append("research_file", researchFile);
  }
  formData.append("profile", JSON.stringify(profile));

  const res = await fetch(makeUrl("recommendation"), {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to get recommendation");
  }

  return await res.json();
};

// -----------------------
// API STATUS
// -----------------------
export const getApiStatus = async () => {
  const res = await fetch(makeUrl("api/health"));
  if (!res.ok) {
    throw new Error("API health check failed");
  }
  return await res.json();
};