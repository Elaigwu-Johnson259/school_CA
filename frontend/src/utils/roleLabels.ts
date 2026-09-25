import type { UserRole } from "@/types/auth";

/**
 * Human-readable labels for the raw role enum values, so the UI never
 * shows a normal user something like "SCHOOL_ADMIN" verbatim.
 */
const ROLE_LABELS: Record<UserRole, string> = {
  SUPER_ADMIN: "Super Administrator",
  SCHOOL_ADMIN: "School Administrator",
  TEACHER: "Teacher",
  STUDENT: "Student",
};

export function roleLabel(role: UserRole): string {
  return ROLE_LABELS[role] ?? role;
}
