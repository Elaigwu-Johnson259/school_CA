import axios from "axios";
import { apiClient } from "./client";
import type { AccessTokenResponse, AuthenticatedUser, TokenResponse } from "@/types/auth";

export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", { email, password });
  return response.data;
}

export async function fetchCurrentUser(): Promise<AuthenticatedUser> {
  const response = await apiClient.get<AuthenticatedUser>("/auth/me");
  return response.data;
}

export async function refreshAccessToken(refreshToken: string): Promise<AccessTokenResponse> {
  // Plain axios (not apiClient) — this call must NOT go through the
  // request/response interceptors in client.ts, or a failed refresh could
  // try to refresh itself in an infinite loop.
  const response = await axios.post<AccessTokenResponse>(
    `${apiClient.defaults.baseURL}/auth/refresh`,
    { refresh_token: refreshToken }
  );
  return response.data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout", { refresh_token: refreshToken });
}
