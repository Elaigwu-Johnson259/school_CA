import { apiClient } from "./client";

export type ExaminationStatus = "DRAFT" | "PUBLISHED" | "CLOSED";
export type QuestionType = "OBJECTIVE" | "SUBJECTIVE";
export type ReferenceMaterialType = "TYPED_ANSWER" | "MARKING_GUIDANCE" | "UPLOAD" | "HANDWRITTEN" | "WORKED_SOLUTION";

export interface Examination {
  id: number;
  school_id: number;
  academic_session_id: number;
  term_id: number;
  school_class_id: number;
  subject_id: number;
  created_by_id: number;
  title: string;
  description: string | null;
  instructions: string | null;
  examination_date: string | null;
  duration_minutes: number | null;
  maximum_score: number;
  status: ExaminationStatus;
  created_at: string;
  updated_at: string;
}

export interface ExaminationQuestion {
  id: number;
  examination_id: number;
  question_number: string;
  section: string | null;
  question_text: string;
  question_type: QuestionType;
  maximum_marks: number;
  display_order: number;
  instructions: string | null;
  correct_option: string | null;
  expected_concepts: string | null;
  key_points: string | null;
  acceptable_alternatives: string | null;
  partial_credit_guidance: string | null;
  marking_guidance: string | null;
  teacher_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReferenceMaterial {
  id: number;
  question_id: number;
  material_type: ReferenceMaterialType;
  title: string | null;
  text_content: string | null;
  original_filename: string | null;
  content_type: string | null;
  file_size: number | null;
  notes: string | null;
  created_at: string;
}

export interface StudentScript {
  id: number;
  school_id: number;
  examination_id: number;
  student_id: number;
  assessment_type_id: number | null;
  original_filename: string;
  content_type: string | null;
  file_size: number | null;
  checksum_sha256: string | null;
  status: string;
  processing_error: string | null;
  processed_at: string | null;
  approved_at: string | null;
  approved_by_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface StudentAnswer {
  id: number;
  script_id: number;
  question_id: number;
  extracted_text: string | null;
  extraction_status: string | null;
  ai_proposed_score: number | null;
  ai_evidence: string | null;
  ai_confidence: number | null;
  teacher_final_score: number | null;
  teacher_adjustment: number | null;
  teacher_review_notes: string | null;
  review_status: string;
}

export async function fetchExaminations(): Promise<Examination[]> {
  const response = await apiClient.get<Examination[]>("/academic/examinations");
  return response.data;
}

export async function createExamination(payload: {
  academic_session_id: number;
  term_id: number;
  school_class_id: number;
  subject_id: number;
  title: string;
  description?: string;
  instructions?: string;
  examination_date?: string;
  duration_minutes?: number;
  maximum_score: number;
  status?: ExaminationStatus;
}): Promise<Examination> {
  const response = await apiClient.post<Examination>("/academic/examinations", payload);
  return response.data;
}

export async function updateExamination(id: number, payload: Partial<Omit<Examination, "id" | "school_id" | "created_by_id" | "created_at" | "updated_at">>): Promise<Examination> {
  const response = await apiClient.patch<Examination>(`/academic/examinations/${id}`, payload);
  return response.data;
}

export async function fetchQuestions(examinationId: number): Promise<ExaminationQuestion[]> {
  const response = await apiClient.get<ExaminationQuestion[]>(`/academic/examinations/${examinationId}/questions`);
  return response.data;
}

export async function createQuestion(examinationId: number, payload: Omit<ExaminationQuestion, "id" | "examination_id" | "created_at" | "updated_at">): Promise<ExaminationQuestion> {
  const response = await apiClient.post<ExaminationQuestion>(`/academic/examinations/${examinationId}/questions`, payload);
  return response.data;
}

export async function createReference(questionId: number, payload: { material_type: ReferenceMaterialType; title?: string; text_content?: string; notes?: string }): Promise<ReferenceMaterial> {
  const response = await apiClient.post<ReferenceMaterial>(`/academic/questions/${questionId}/references`, payload);
  return response.data;
}

export async function uploadReference(questionId: number, file: File, materialType: ReferenceMaterialType, title?: string): Promise<ReferenceMaterial> {
  const form = new FormData();
  form.append("file", file);
  form.append("material_type", materialType);
  if (title) form.append("title", title);
  const response = await apiClient.post<ReferenceMaterial>(`/academic/questions/${questionId}/references/upload`, form);
  return response.data;
}

export async function uploadQuestionPaper(examinationId: number, file: File): Promise<void> {
  const form = new FormData();
  form.append("file", file);
  await apiClient.post(`/academic/examinations/${examinationId}/question-paper`, form);
}

export async function uploadStudentScript(examinationId: number, studentId: number, assessmentTypeId: number, file: File): Promise<StudentScript> {
  const form = new FormData();
  form.append("student_id", String(studentId));
  form.append("assessment_type_id", String(assessmentTypeId));
  form.append("file", file);
  const response = await apiClient.post<StudentScript>(`/academic/examinations/${examinationId}/scripts`, form);
  return response.data;
}

export async function fetchStudentScripts(examinationId: number): Promise<StudentScript[]> {
  const response = await apiClient.get<StudentScript[]>(`/academic/examinations/${examinationId}/scripts`);
  return response.data;
}

export async function fetchScriptAnswers(scriptId: number): Promise<StudentAnswer[]> {
  const response = await apiClient.get<StudentAnswer[]>(`/academic/scripts/${scriptId}/answers`);
  return response.data;
}

export async function startScriptMarking(scriptId: number): Promise<StudentScript> {
  const response = await apiClient.post<StudentScript>(`/academic/scripts/${scriptId}/ai-mark`);
  return response.data;
}

export async function reviewScriptAnswer(answerId: number, payload: { teacher_final_score: number; teacher_review_notes: string | null; extracted_text: string; review_status: "REVIEWED" }): Promise<StudentAnswer> {
  const response = await apiClient.patch<StudentAnswer>(`/academic/answers/${answerId}/review`, payload);
  return response.data;
}

export async function approveStudentScript(scriptId: number, assessmentTypeId: number): Promise<StudentScript> {
  const response = await apiClient.post<StudentScript>(`/academic/scripts/${scriptId}/approve`, { confirm: true, assessment_type_id: assessmentTypeId });
  return response.data;
}

export async function fetchQuestionReferences(questionId: number): Promise<ReferenceMaterial[]> {
  const response = await apiClient.get<ReferenceMaterial[]>(`/academic/questions/${questionId}/references`);
  return response.data;
}

export async function fetchReferenceFile(referenceId: number): Promise<Blob> {
  const response = await apiClient.get<Blob>(`/academic/references/${referenceId}/file`, { responseType: "blob" });
  return response.data;
}

export async function fetchScriptFile(scriptId: number): Promise<Blob> {
  const response = await apiClient.get<Blob>(`/academic/scripts/${scriptId}/file`, { responseType: "blob" });
  return response.data;
}
