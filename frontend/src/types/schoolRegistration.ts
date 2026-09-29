import type { AuthenticatedUser } from "./auth";
import type { School } from "./school";

export interface SchoolRegistrationRequest {
  school_name: string;
  school_email: string;
  phone?: string;
  address?: string;
  state?: string;
  country?: string;
  admin_email: string;
  password: string;
}

export interface SchoolRegistrationResponse {
  message: string;
  school: School;
  admin: AuthenticatedUser;
}

/** Fields a SCHOOL_ADMIN may edit on their own school. All optional — send only what changed. */
export interface SchoolUpdateRequest {
  name?: string;
  email?: string;
  phone?: string;
  address?: string;
  state?: string;
  country?: string;
  motto?: string;
  website?: string;
  principal_name?: string;
  primary_color?: string;
  secondary_color?: string;
}
