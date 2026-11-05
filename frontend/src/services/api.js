
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

let refreshPromise = null;

function getAccessToken() {
  return sessionStorage.getItem(ACCESS_TOKEN_KEY);
}

function clearTokens() {
  sessionStorage.removeItem(ACCESS_TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

function saveTokens(access, refresh) {
  if (access) {
    sessionStorage.setItem(ACCESS_TOKEN_KEY, access);
  }

  if (refresh) {
    sessionStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
}

function buildHeaders(options = {}) {
  const headers = new Headers(options.headers || {});
  const isFormData = options.body instanceof FormData;

  if (options.body && !isFormData && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (options.auth !== false) {
    const access = getAccessToken();

    if (access && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${access}`);
    }
  }

  return headers;
}

async function refreshAccessToken() {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    const refresh = sessionStorage.getItem(REFRESH_TOKEN_KEY);

    if (!refresh) {
      clearTokens();
      throw new Error("Your session has expired. Please log in again.");
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/refresh/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh }),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data.access) {
      clearTokens();
      throw new Error("Your session has expired. Please log in again.");
    }

    saveTokens(data.access, data.refresh || refresh);

    return data.access;
  })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

function getErrorMessage(data, status) {
  if (typeof data?.detail === "string") {
    return data.detail;
  }

  const messages = Object.values(data || {})
    .flat(Infinity)
    .filter(value => typeof value === "string");

  return messages.join(" ") || `Request failed (${status})`;
}

async function sendRequest(endpoint, options = {}, retry = true) {
  const {
    auth,
    ...fetchOptions
  } = options;

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers: buildHeaders({ ...options, auth }),
  });

  if (
    response.status === 401 &&
    retry &&
    auth !== false &&
    sessionStorage.getItem(REFRESH_TOKEN_KEY)
  ) {
    const newAccess = await refreshAccessToken();

    const headers = new Headers(fetchOptions.headers || {});
    headers.set("Authorization", `Bearer ${newAccess}`);

    return sendRequest(
      endpoint,
      {
        ...fetchOptions,
        headers,
        auth: true,
      },
      false
    );
  }

  return response;
}

export async function apiRequest(endpoint, options = {}) {
  const response = await sendRequest(endpoint, options);

  if (response.status === 204 || response.status === 205) {
    return null;
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(getErrorMessage(data, response.status));
  }

  return data;
}

export async function apiUpload(endpoint, formData, options = {}) {
  if (!(formData instanceof FormData)) {
    throw new Error("File upload requires FormData.");
  }

  return apiRequest(endpoint, {
    ...options,
    method: options.method || "POST",
    body: formData,
  });
}

export async function apiDownload(endpoint, options = {}) {
  const response = await sendRequest(endpoint, options);

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(getErrorMessage(data, response.status));
  }

  return response.blob();
}
