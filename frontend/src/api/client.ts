import axios, { type InternalAxiosRequestConfig } from "axios";
import { refreshAccessToken } from "./auth";
import { getStoredTokens, setStoredTokens, clearStoredTokens } from "@/utils/tokenStorage";

/**
 * Shared Axios instance for all API calls.
 * Base URL comes from VITE_API_BASE_URL (see .env.example).
 */
export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api",
});

// Attach the current access token to every outgoing request, if we have one.
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const tokens = getStoredTokens();
  if (tokens?.accessToken) {
    config.headers.Authorization = `Bearer ${tokens.accessToken}`;
  }
  return config;
});

let refreshInFlight: Promise<string> | null = null;

// On a 401, try once to use the refresh token to get a new access token
// and retry the original request. If that also fails, clear stored
// tokens so the app falls back to the login page.
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retried?: boolean;
    };

    const isAuthEndpoint =
      originalRequest?.url?.includes("/auth/login") ||
      originalRequest?.url?.includes("/auth/refresh");

    if (error.response?.status === 401 && !originalRequest._retried && !isAuthEndpoint) {
      originalRequest._retried = true;
      const tokens = getStoredTokens();

      if (!tokens?.refreshToken) {
        clearStoredTokens();
        return Promise.reject(error);
      }

      try {
        // Share one in-flight refresh across concurrent failed requests,
        // rather than firing a separate refresh call for each.
        if (!refreshInFlight) {
          refreshInFlight = refreshAccessToken(tokens.refreshToken).then((res) => {
            setStoredTokens({ accessToken: res.access_token, refreshToken: tokens.refreshToken });
            return res.access_token;
          });
        }
        const newAccessToken = await refreshInFlight;
        refreshInFlight = null;

        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        refreshInFlight = null;
        clearStoredTokens();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);
