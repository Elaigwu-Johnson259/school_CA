import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createScore,
  fetchAssessmentTypes,
  fetchClassSubjects,
  fetchClasses,
  fetchResults,
  fetchScores,
  fetchSessions,
  fetchSubjects,
  fetchTeacherAssignments,
  fetchTerms,
  updateScore,
} from "@/api/academic";
import { fetchStudentEnrollments, fetchStudents } from "@/api/students";
import { useAuth } from "@/context/AuthContext";
import type { Result } from "@/api/academic";

export function ScoresPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState("");
  const [termId, setTermId] = useState("");
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const sessionsQuery = useQuery({ queryKey: ["sessions"], queryFn: fetchSessions });
  const termsQuery = useQuery({
    queryKey: ["scores-terms", sessionId],
    queryFn: () => fetchTerms(Number(sessionId)),
    enabled: Boolean(sessionId),
  });
  const classesQuery = useQuery({ queryKey: ["classes"], queryFn: fetchClasses });
  const subjectsQuery = useQuery({ queryKey: ["subjects"], queryFn: fetchSubjects });
  const assessmentQuery = useQuery({ queryKey: ["assessment-types"], queryFn: fetchAssessmentTypes });
  const assignmentsQuery = useQuery({
    queryKey: ["teacher-assignments"],
    queryFn: fetchTeacherAssignments,
    enabled: user?.role === "TEACHER",
  });
  const enrollmentsQuery = useQuery({
    queryKey: ["score-enrollments", sessionId, classId],
    queryFn: fetchStudentEnrollments,
    enabled: Boolean(sessionId && classId),
  });
  const studentsQuery = useQuery({ queryKey: ["students"], queryFn: fetchStudents });
  const classSubjectsQuery = useQuery({
    queryKey: ["class-subjects", classId],
    queryFn: () => fetchClassSubjects(Number(classId)),
    enabled: Boolean(classId),
  });
  const scoresQuery = useQuery({
    queryKey: ["score-entries", studentIdList(enrollmentsQuery.data, sessionId), subjectId, termId, classId],
    queryFn: () => fetchScores({ term_id: Number(termId), subject_id: Number(subjectId), school_class_id: Number(classId) }),
    enabled: Boolean(termId && subjectId && classId),
  });
  const resultsQuery = useQuery({
    queryKey: ["score-results", subjectId, termId, classId],
    queryFn: () => fetchResults({ term_id: Number(termId) }),
    enabled: Boolean(termId && subjectId && classId),
  });

  const allowedClassIds = useMemo(() => {
    if (user?.role !== "TEACHER") return null;
    return new Set((assignmentsQuery.data ?? []).map((item) => item.school_class_id));
  }, [assignmentsQuery.data, user?.role]);

  const allowedSubjectIds = useMemo(() => {
    if (user?.role !== "TEACHER" || !classId) return null;
    return new Set(
      (assignmentsQuery.data ?? [])
        .filter((item) => item.school_class_id === Number(classId))
        .map((item) => item.subject_id),
    );
  }, [assignmentsQuery.data, classId, user?.role]);

  const classes = (classesQuery.data ?? []).filter((item) => !allowedClassIds || allowedClassIds.has(item.id));
  const subjects = (subjectsQuery.data ?? []).filter((item) => {
    if (!classId) return false;
    const linked = new Set((classSubjectsQuery.data ?? []).map((link) => link.subject_id));
    if (!linked.has(item.id)) return false;
    return !allowedSubjectIds || allowedSubjectIds.has(item.id);
  });

  const students = useMemo(() => {
    const ids = new Set(
      (enrollmentsQuery.data ?? [])
        .filter((enrollment) => enrollment.academic_session_id === Number(sessionId) && enrollment.school_class_id === Number(classId))
        .map((enrollment) => enrollment.student_id),
    );
    return (studentsQuery.data ?? []).filter((student) => ids.has(student.id));
  }, [enrollmentsQuery.data, studentsQuery.data, sessionId, classId]);

  const scoreMap = useMemo(() => {
    const map = new Map<string, { id: number; value: number }>();
    for (const score of scoresQuery.data ?? []) {
      map.set(`${score.student_id}:${score.assessment_type_id}`, { id: score.id, value: score.value });
    }
    return map;
  }, [scoresQuery.data]);

  const resultMap = useMemo(() => {
    const map = new Map<number, Result>();
    for (const result of resultsQuery.data ?? []) {
      if (result.subject_id === Number(subjectId)) map.set(result.student_id, result);
    }
    return map;
  }, [resultsQuery.data, subjectId]);

  const assessments = useMemo(
    () => [...(assessmentQuery.data ?? [])].sort((a, b) => a.display_order - b.display_order),
    [assessmentQuery.data],
  );

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!termId || !classId || !subjectId || !sessionId) throw new Error("Select session, term, class and subject first.");
      if (user?.role === "TEACHER" && !allowedSubjectIds?.has(Number(subjectId))) {
        throw new Error("You are not assigned to this class and subject.");
      }
      if (scoresQuery.isLoading || scoresQuery.isFetching) {
        throw new Error("Existing scores are still loading. Please wait a moment and try again.");
      }
      if (scoresQuery.isError) {
        throw new Error("Unable to load existing scores. Please refresh the page and try again.");
      }
      for (const student of students) {
        for (const assessment of assessments) {
          const key = `${student.id}:${assessment.id}`;
          const raw = drafts[key];
          if (raw === undefined || raw.trim() === "") continue;
          const value = Number(raw);
          if (!Number.isFinite(value) || value < 0 || value > assessment.max_score) {
            throw new Error(`${assessment.name} for ${student.first_name} must be between 0 and ${assessment.max_score}.`);
          }
          const existing = scoreMap.get(key);
          if (existing) {
            if (existing.value !== value) await updateScore(existing.id, value);
          } else {
            await createScore({
              student_id: student.id,
              subject_id: Number(subjectId),
              school_class_id: Number(classId),
              term_id: Number(termId),
              assessment_type_id: assessment.id,
              value,
            });
          }
        }
      }
    },
    onSuccess: async () => {
      setMessage("Scores saved. Results recalculated automatically.");
      setError("");
      setDrafts({});
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["score-entries"] }),
        queryClient.invalidateQueries({ queryKey: ["score-results"] }),
      ]);
    },
    onError: (err: Error) => {
      setMessage("");
      setError(err.message);
    },
  });

  function scoreValue(studentId: number, assessmentId: number) {
    const key = `${studentId}:${assessmentId}`;
    return drafts[key] ?? (scoreMap.get(key)?.value.toString() ?? "");
  }

  function setScore(studentId: number, assessmentId: number, value: string) {
    const assessment = assessments.find((item) => item.id === assessmentId);

    if (value !== "" && assessment) {
      const numericValue = Number(value);

      if (!Number.isFinite(numericValue) || numericValue < 0 || numericValue > assessment.max_score) {
        setError(`${assessment.name} must be between 0 and ${assessment.max_score}.`);
        return;
      }
    }

    setDrafts((current) => ({ ...current, [`${studentId}:${assessmentId}`]: value }));
    setMessage("");
    setError("");
  }

  const canShowTable = Boolean(sessionId && termId && classId && subjectId);

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header>
          <Link to="/dashboard" className="inline-flex text-sm font-medium text-slate-600 hover:text-slate-900">← Back to Dashboard</Link>
          <p className="mt-5 text-sm font-medium text-slate-500">Academic scoring</p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">CA & Exam Scores</h1>
          <p className="mt-2 text-slate-600">Enter the actual marks awarded. CA totals, totals, grades and positions are calculated by the system.</p>
        </header>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 md:grid-cols-4">
            <Select label="Academic session" value={sessionId} onChange={(value) => { setSessionId(value); setTermId(""); }} options={(sessionsQuery.data ?? []).map((item) => [item.id, item.name])} />
            <Select label="Term" value={termId} disabled={!sessionId} onChange={setTermId} options={(termsQuery.data ?? []).map((item) => [item.id, item.name])} />
            <Select label="Assigned class" value={classId} onChange={(value) => { setClassId(value); setSubjectId(""); }} options={classes.map((item) => [item.id, item.name])} />
            <Select label="Assigned subject" value={subjectId} disabled={!classId} onChange={setSubjectId} options={subjects.map((item) => [item.id, item.name])} />
          </div>
        </section>

        {canShowTable && (
          <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
            <div className="border-b border-slate-200 px-5 py-4">
              <h2 className="font-semibold text-slate-900">Student score entry</h2>
              <p className="mt-1 text-xs text-slate-500">Score entry is manual. The calculated columns are read-only.</p>
            </div>
            {students.length === 0 ? (
              <p className="p-6 text-sm text-slate-500">No students are enrolled in this class for the selected session.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">Student</th>
                      {assessments.map((assessment) => <th key={assessment.id} className="px-3 py-3 text-left text-xs font-semibold uppercase text-slate-500">{assessment.name} /{assessment.max_score}</th>)}
                      <th className="px-3 py-3 text-left text-xs font-semibold uppercase text-slate-500">CA Total /30</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold uppercase text-slate-500">Total /100</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold uppercase text-slate-500">Grade</th>
                      <th className="px-3 py-3 text-left text-xs font-semibold uppercase text-slate-500">Position</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {students.map((student) => {
                      const ca = assessments.filter((item) => item.category === "CA").reduce((sum, item) => sum + Number(scoreValue(student.id, item.id) || 0), 0);
                      const exam = assessments.filter((item) => item.category === "EXAM").reduce((sum, item) => sum + Number(scoreValue(student.id, item.id) || 0), 0);
                      const result = resultMap.get(student.id);
                      return (
                        <tr key={student.id}>
                          <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-slate-900">{student.first_name} {student.last_name}<span className="block text-xs font-normal text-slate-500">{student.admission_number}</span></td>
                          {assessments.map((assessment) => <td key={assessment.id} className="px-3 py-3"><input type="number" min={0} max={assessment.max_score} step="0.01" value={scoreValue(student.id, assessment.id)} onChange={(e) => setScore(student.id, assessment.id, e.target.value)} className="w-24 rounded-md border border-slate-300 px-2 py-1.5 text-sm" /></td>)}
                          <td className="px-3 py-3 text-sm font-semibold text-slate-700">{ca}/30</td>
                          <td className="px-3 py-3 text-sm font-semibold text-slate-900">{result?.total ?? (ca + exam)}/100</td>
                          <td className="px-3 py-3 text-sm font-semibold text-slate-700">{result?.grade ?? "—"}</td>
                          <td className="px-3 py-3 text-sm font-semibold text-slate-700">{result?.subject_position ? ordinal(result.subject_position) : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
            <div className="flex items-center justify-between border-t border-slate-200 px-5 py-4">
              <div>{error && <p className="text-sm text-red-700">{error}</p>}{message && <p className="text-sm text-green-700">{message}</p>}</div>
              <button type="button" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending || students.length === 0} className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50">{saveMutation.isPending ? "Saving..." : "Save / Update Scores"}</button>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}

function studentIdList(data: { student_id: number }[] | undefined, sessionId: string) {
  return `${sessionId}:${(data ?? []).map((item) => item.student_id).join(",")}`;
}

function ordinal(value: number) {
  const mod100 = value % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${value}th`;
  switch (value % 10) { case 1: return `${value}st`; case 2: return `${value}nd`; case 3: return `${value}rd`; default: return `${value}th`; }
}

function Select({ label, value, onChange, options, disabled = false }: { label: string; value: string; onChange: (value: string) => void; options: [number, string][]; disabled?: boolean }) {
  return <label className="block"><span className="text-sm font-medium text-slate-700">{label}</span><select value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm disabled:bg-slate-100"><option value="">Select {label.toLowerCase()}</option>{options.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label>;
}
