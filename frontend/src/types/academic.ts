import type { TermName } from "./enums";

export interface AcademicSession {
  id: number;
  school_id: number;
  name: string;
  is_current: boolean;
  created_at: string;
}

export interface Term {
  id: number;
  academic_session_id: number;
  name: TermName;
  is_current: boolean;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export interface SchoolClass {
  id: number;
  school_id: number;
  name: string;
  created_at: string;
}
