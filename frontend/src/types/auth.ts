export type UserRole = "SUPER_ADMIN" | "SCHOOL_ADMIN" | "TEACHER" | "STUDENT";

export interface AuthenticatedUser {
  id: number;
  email: string;
  role: UserRole;
  school_id: number | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthenticatedUser;
}

export interface AccessTokenResponse {
  access_token: string;
  token_type: string;
}
