const BASE = import.meta.env.VITE_API_URL || "";

export const getToken = () => localStorage.getItem("token");

async function request(path, { method = "GET", body, params } = {}) {
  const qs = params
    ? "?" + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== "" && v != null)).toString()
    : "";
  const res = await fetch(`${BASE}/api${path}${qs}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    const msg = Array.isArray(d) ? d.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ") : d;
    const err = new Error(msg || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  get: (p, params) => request(p, { params }),
  post: (p, body) => request(p, { method: "POST", body: body ?? {} }),
  put: (p, body) => request(p, { method: "PUT", body: body ?? {} }),
  del: (p) => request(p, { method: "DELETE" }),
};

export const EMOJI = {
  Breakfast: "🥣", Lunch: "🥗", Dinner: "🍛", Snacks: "🥜", Drinks: "🥤",
  Supplements: "💊", Pantry: "🫒", Fresh: "🐟",
};
export const emojiFor = (category) => EMOJI[category] || "🍽️";
