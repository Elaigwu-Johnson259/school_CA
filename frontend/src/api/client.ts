import axios from "axios";

/**
 * Shared Axios instance for all API calls.
 * Base URL comes from VITE_API_BASE_URL (see .env.example).
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
});
