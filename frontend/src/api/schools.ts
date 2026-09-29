import { apiClient } from "./client";
import type { School } from "@/types/school";
import type {
  SchoolRegistrationRequest,
  SchoolRegistrationResponse,
  SchoolUpdateRequest,
} from "@/types/schoolRegistration";

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

/** SCHOOL_ADMIN only. Updates only the fields included in `updates`. */
export async function updateMySchool(updates: SchoolUpdateRequest): Promise<School> {
  const response = await apiClient.patch<School>("/schools/me", updates);
  return response.data;
}

/**
 * Public endpoint — no auth token is attached (there isn't one yet).
 * Creates a brand-new School plus its first SCHOOL_ADMIN.
 */
export async function registerSchool(
  payload: SchoolRegistrationRequest
): Promise<SchoolRegistrationResponse> {
  const response = await apiClient.post<SchoolRegistrationResponse>(
    "/schools/register",
    payload
  );
  return response.data;
}
