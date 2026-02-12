const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function apiGet(path, params = {}) {
  // Fix: Handle both absolute URLs (dev) and relative paths (prod)
  const fullUrl = API_BASE.startsWith('http') 
    ? `${API_BASE}${path}`  // Dev: http://localhost:8000/events/today
    : `${API_BASE}${path}`;  // Prod: /api/events/today
  
  const url = API_BASE.startsWith('http')
    ? new URL(fullUrl)  // Absolute URL
    : new URL(fullUrl, window.location.origin);  // Relative path needs base
  
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null) url.searchParams.set(k, v);
  });
  
  const res = await fetch(url.toString(), { headers: { "Accept": "application/json" } });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`GET ${path} failed: ${res.status} ${text}`);
  }
  return res.json();
}