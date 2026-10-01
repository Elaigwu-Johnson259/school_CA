import { apiClient } from "./client";
import type { AcademicSession, SchoolClass, Subject, Term } from "@/types/academic";
import type { TermName } from "@/types/enums";

export async function fetchSessions(): Promise<AcademicSession[]> {
  const response = await apiClient.get<AcademicSession[]>("/academic/sessions");
  return response.data;
}

export async function createSession(
  name: string,
  is_current = false,
): Promise<AcademicSession> {
  const response = await apiClient.post<AcademicSession>("/academic/sessions", {
    name,
    is_current,
  });
  return response.data;
}

export async function updateSession(
  sessionId: number,
  updates: {
    name?: string;
    is_current?: boolean;
  },
): Promise<AcademicSession> {
  const response = await apiClient.patch<AcademicSession>(
    `/academic/sessions/${sessionId}`,
    updates,
  );
  return response.data;
}

export async function fetchTerms(sessionId: number): Promise<Term[]> {
  const response = await apiClient.get<Term[]>(
    `/academic/sessions/${sessionId}/terms`,
  );
  return response.data;
}

export async function createTerm(
  sessionId: number,
  payload: {
    name: TermName;
    is_current?: boolean;
    start_date?: string | null;
    end_date?: string | null;
  },
): Promise<Term> {
  const response = await apiClient.post<Term>(
    `/academic/sessions/${sessionId}/terms`,
    payload,
  );
  return response.data;
}

export async function updateTerm(
  termId: number,
  updates: {
    name?: TermName;
    is_current?: boolean;
    start_date?: string | null;
    end_date?: string | null;
  },
): Promise<Term> {
  const response = await apiClient.patch<Term>(
    `/academic/terms/${termId}`,
    updates,
  );
  return response.data;
}

export async function fetchClasses(): Promise<SchoolClass[]> {
  const response = await apiClient.get<SchoolClass[]>("/academic/classes");
  return response.data;
}

export async function createClass(name: string): Promise<SchoolClass> {
  const response = await apiClient.post<SchoolClass>("/academic/classes", {
    name,
  });
  return response.data;
}

export async function createSubject(
  name: string,
  code: string,
): Promise<Subject> {
  const response = await apiClient.post<Subject>("/academic/subjects", {
    name,
    code,
  });
  return response.data;
}

export async function createClassSubject(
  classId: number,
  subjectId: number,
): Promise<{ id: number; school_class_id: number; subject_id: number }> {
  const response = await apiClient.post(
    `/academic/classes/${classId}/subjects`,
    { school_class_id: classId, subject_id: subjectId },
  );
  return response.data;
}

export interface AssessmentType {
  id: number;
  school_id: number;
  name: string;
  category: "CA" | "EXAM";
  max_score: number;
  display_order: number;
}

export interface Score {
  id: number;
  student_id: number;
  subject_id: number;
  school_class_id: number;
  term_id: number;
  assessment_type_id: number;
  value: number;
}

export interface Result {
  id: number;
  student_id: number;
  subject_id: number;
  term_id: number;
  ca_total: number;
  exam_score: number;
  total: number;
  grade: string | null;
  subject_position: number | null;
}

export async function fetchAssessmentTypes(): Promise<AssessmentType[]> {
  const response = await apiClient.get<AssessmentType[]>(
    "/academic/assessment-types",
  );
  return response.data;
}

export async function createScore(payload: {
  student_id: number;
  subject_id: number;
  school_class_id: number;
  term_id: number;
  assessment_type_id: number;
  value: number;
}): Promise<Score> {
  const response = await apiClient.post<Score>("/academic/scores", payload);
  return response.data;
}

export async function calculateResult(
  studentId: number,
  subjectId: number,
  termId: number,
): Promise<Result> {
  const response = await apiClient.post<Result>(
    `/academic/results/calculate?student_id=${studentId}&subject_id=${subjectId}&term_id=${termId}`,
  );
  return response.data;
}

export async function fetchSubjects(): Promise<Subject[]> {
  const response = await apiClient.get<Subject[]>("/academic/subjects");
  return response.data;
}

export interface TeacherAssignment {
  id: number;
  teacher_id: number;
  school_class_id: number;
  subject_id: number;
}

export async function fetchTeacherAssignments(): Promise<TeacherAssignment[]> {
  const response = await apiClient.get<TeacherAssignment[]>('/academic/teacher-assignments');
  return response.data;
}

export async function fetchClassSubjects(classId: number): Promise<{ id: number; school_class_id: number; subject_id: number }[]> {
  const response = await apiClient.get(`/academic/classes/${classId}/subjects`);
  return response.data;
}

export async function fetchScores(filters: {
  student_id?: number;
  subject_id?: number;
  term_id?: number;
  school_class_id?: number;
}): Promise<Score[]> {
  const response = await apiClient.get<Score[]>('/academic/scores', { params: filters });
  return response.data;
}

export async function updateScore(scoreId: number, value: number): Promise<Score> {
  const response = await apiClient.patch<Score>(`/academic/scores/${scoreId}`, { value });
  return response.data;
}

export async function fetchResults(filters: { student_id?: number; term_id?: number }): Promise<Result[]> {
  const response = await apiClient.get<Result[]>('/academic/results', { params: filters });
  return response.data;
}

export async function fetchReportCard(studentId: number, termId: number) {
  const response = await apiClient.get(`/academic/report-cards/${studentId}/${termId}`);
  return response.data as {
    id: number;
    student_id: number;
    term_id: number;
    total_marks: number;
    average: number;
    overall_grade: string | null;
    class_position: number | null;
    number_of_students: number | null;
    status: string;
  };
}

export interface Teacher {
  id: number;
  school_id: number;
  first_name: string;
  last_name: string;
  email: string | null;
  phone: string | null;
  employee_id: string | null;
  status: string;
}

export async function fetchTeachers(): Promise<Teacher[]> {
  const response = await apiClient.get<Teacher[]>('/academic/teachers');
  return response.data;
}

export async function createTeacher(payload: {
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  employee_id?: string;
  password?: string;
}): Promise<Teacher> {
  const response = await apiClient.post<Teacher>('/academic/teachers', payload);
  return response.data;
}

export async function createTeacherAssignment(payload: {
  teacher_id: number;
  school_class_id: number;
  subject_id: number;
}): Promise<TeacherAssignment> {
  const response = await apiClient.post<TeacherAssignment>('/academic/teacher-assignments', payload);
  return response.data;
}
