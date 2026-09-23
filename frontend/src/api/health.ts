import { apiClient } from "./client";

export async function checkHealth() {
  const res = await apiClient.get("/health");
  return res.data;
}
