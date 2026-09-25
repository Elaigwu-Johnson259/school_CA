import { apiClient } from "./client";
import type { School } from "@/types/school";

/**
 * Returns the authenticated user's own school. Only meaningful for
 * school-bound accounts (SCHOOL_ADMIN/TEACHER/STUDENT) — the backend
 * returns 403 for a SUPER_ADMIN, since they don't have a single "home"
 * school (see backend/app/core/tenancy.py).
 */
export async function fetchMySchool(): Promise<School> {
  const response = await apiClient.get<School>("/schools/me");
  return response.data;
}
