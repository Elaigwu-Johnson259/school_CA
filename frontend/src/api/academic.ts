import { apiClient } from "./client";
import type { AcademicSession, Term } from "@/types/academic";
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
