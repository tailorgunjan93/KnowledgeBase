import axios from 'axios';

const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 30000,
});

// Store auth token in memory as well (in addition to localStorage)
let authToken = null;

// Export a function to set the auth token globally
export const setAuthToken = (token) => {
  authToken = token;
  if (token) {
    httpClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete httpClient.defaults.headers.common['Authorization'];
  }
};

// Request interceptor: attach token/settings if needed
httpClient.interceptors.request.use((config) => {
  // Use in-memory token if available, otherwise fallback to sessionStorage
  const token = authToken || sessionStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Attach API key from localStorage if it exists
  const apiKey = localStorage.getItem('groq_api_key');
  if (apiKey) config.headers['X-API-Key'] = apiKey;

  return config;
});

// Response interceptor: normalise errors
httpClient.interceptors.response.use(
  (res) => res,
  (err) => {
    // Log full error to console for debugging
    console.error('API Error:', err);
    if (err.response) {
      console.error('Status:', err.response.status);
      console.error('Data:', err.response.data);
    }
    // If backend returns a structured error like { error: "msg" }
    const message = err.response?.data?.error || err.response?.data?.detail || err.message || 'Unknown error';
    return Promise.reject(new Error(message));
  }
);

export default httpClient;
export { httpClient };
