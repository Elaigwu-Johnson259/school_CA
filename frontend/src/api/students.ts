import { apiClient } from "./client";
import type { Gender } from "@/types/enums";
import type { Student, StudentEnrollment } from "@/types/student";

export interface StudentPayload {
  admission_number: string;
  first_name: string;
  middle_name?: string | null;
  last_name: string;
  gender?: Gender | null;
  date_of_birth?: string | null;
  guardian_name?: string | null;
  guardian_phone?: string | null;
  address?: string | null;
}

export async function fetchStudents(): Promise<Student[]> {
  const response = await apiClient.get<Student[]>("/academic/students");
  return response.data;
}

export async function fetchStudent(studentId: number): Promise<Student> {
  const response = await apiClient.get<Student>(
    `/academic/students/${studentId}`,
  );
  return response.data;
}

export async function createStudent(
  payload: StudentPayload,
): Promise<Student> {
  const response = await apiClient.post<Student>(
    "/academic/students",
    payload,
  );
  return response.data;
}

export async function updateStudent(
  studentId: number,
  payload: Partial<StudentPayload>,
): Promise<Student> {
  const response = await apiClient.patch<Student>(
    `/academic/students/${studentId}`,
    payload,
  );
  return response.data;
}

export async function fetchStudentEnrollments(): Promise<StudentEnrollment[]> {
  const response = await apiClient.get<StudentEnrollment[]>(
    "/academic/student-enrollments",
  );
  return response.data;
}

export async function createStudentEnrollment(
  payload: Omit<StudentEnrollment, "id">,
): Promise<StudentEnrollment> {
  const response = await apiClient.post<StudentEnrollment>(
    "/academic/student-enrollments",
    payload,
  );
  return response.data;
}

export async function deleteStudentEnrollment(
  enrollmentId: number,
): Promise<void> {
  await apiClient.delete(`/academic/student-enrollments/${enrollmentId}`);
}
