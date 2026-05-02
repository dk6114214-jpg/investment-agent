const BASE_URL =
  process.env.REACT_APP_API_BASE ||
  "https://web-production-fd1ce.up.railway.app";

// -----------------------
// UPLOAD CSV
// -----------------------
export const uploadCsv = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/market/upload`, {
    method: "POST",
    body: formData,
  });

  return await res.json();
};

// -----------------------
// GET RECOMMENDATION (FIXED)
// -----------------------
export const getRecommendation = async (file, profile) => {
  if (!file) {
    throw new Error("CSV file required");
  }

  const formData = new FormData();
  formData.append("file", file);

  // profile ko string bana ke bhejo
  formData.append("data", JSON.stringify(profile));

  const res = await fetch(`${BASE_URL}/recommendation`, {
    method: "POST",
    body: formData,
  });

  const data = await res.json();

  if (data.error) {
    throw new Error(data.error);
  }

  return data;
};

// -----------------------
// API STATUS
// -----------------------
export const getApiStatus = async () => {
  const res = await fetch(`${BASE_URL}/`);
  return await res.json();
};