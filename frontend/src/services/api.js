
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiRequest(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
  });

  if (response.status === 204 || response.status === 205) {
    return null;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = Object.values(data)
      .flat()
      .filter(value => typeof value === "string")
      .join(" ");

    throw new Error(message || `Request failed (${response.status})`);
  }

  return data;
}
