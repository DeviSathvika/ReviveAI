const API_BASE_URL = "https://reviveai-backend-yand.onrender.com";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();

    throw new Error(
      `ReviveAI API error ${response.status}: ${message}`
    );
  }

  return response.json();
}

export function getDashboard() {
  return request("/api/dashboard");
}

export function getTransactions() {
  return request("/api/transactions");
}

export function analyzeTransaction(transactionId) {
  return request(
    `/api/transactions/${transactionId}/analyze`
  );
}