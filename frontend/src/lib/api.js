const BASE = "/api";

/** Inventory blueprint is mounted at `/inventory`, not under `/api`. */
function resolveUrl(path) {
  const p = path.startsWith("/") ? path : `/${path}`;
  if (p.startsWith("/inventory/")) {
    return p;
  }
  return `${BASE}${p}`;
}

async function request(path, options = {}) {
  const res = await fetch(resolveUrl(path), {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || res.statusText);
  }
  return res.json();
}

export function get(path) {
  return request(path);
}

export function post(path, data) {
  return request(path, { method: "POST", body: JSON.stringify(data) });
}

export function put(path, data) {
  return request(path, { method: "PUT", body: JSON.stringify(data) });
}

export function patch(path, data) {
  return request(path, { method: "PATCH", body: JSON.stringify(data) });
}

export function del(path) {
  return request(path, { method: "DELETE" });
}
