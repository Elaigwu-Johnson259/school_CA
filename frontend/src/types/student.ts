import type { Gender, PersonStatus } from "./enums";

export interface Student {
  id: number;
  school_id: number;
  admission_number: string;
  first_name: string;
  middle_name: string | null;
  last_name: string;
  gender: Gender | null;
  date_of_birth: string | null;
  guardian_name: string | null;
  guardian_phone: string | null;
  address: string | null;
  status: PersonStatus;
}

export interface StudentEnrollment {
  id: number;
  student_id: number;
  school_class_id: number;
  academic_session_id: number;
}
