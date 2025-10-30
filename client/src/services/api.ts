import axios from "axios";

const DEFAULT_API_BASE_URL = "http://localhost:8000";
const rawBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
export const API_BASE_URL = (rawBaseUrl && rawBaseUrl.length > 0 ? rawBaseUrl : DEFAULT_API_BASE_URL).replace(/\/+$/, "");

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default api;
