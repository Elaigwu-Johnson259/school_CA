import axios from "axios";
import { apiClient } from "./client";
import type { AccessTokenResponse, AuthenticatedUser, TokenResponse } from "@/types/auth";

export async function login(identifier: string, password: string): Promise<TokenResponse> {
  const response = await apiClient.post<TokenResponse>("/auth/login", { identifier, password });
  return response.data;
}

export async function fetchCurrentUser(): Promise<AuthenticatedUser> {
  const response = await apiClient.get<AuthenticatedUser>("/auth/me");
  return response.data;
}

export async function refreshAccessToken(refreshToken: string): Promise<AccessTokenResponse> {
  const response = await axios.post<AccessTokenResponse>(
    `${apiClient.defaults.baseURL}/auth/refresh`,
    { refresh_token: refreshToken }
  );
  return response.data;
}

export async function logout(refreshToken: string): Promise<void> {
  await apiClient.post("/auth/logout", { refresh_token: refreshToken });
}
