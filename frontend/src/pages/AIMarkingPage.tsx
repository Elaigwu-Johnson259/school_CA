import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchAssessmentTypes, fetchClassSubjects, fetchClasses, fetchSessions, fetchSubjects, fetchTerms } from "@/api/academic";
import {
  approveStudentScript,
  fetchExaminations,
  fetchQuestionReferences,
  fetchQuestions,
  fetchReferenceFile,
  fetchScriptAnswers,
  fetchScriptFile,
  fetchStudentScripts,
  reviewScriptAnswer,
  startScriptMarking,
  uploadStudentScript,
  type ReferenceMaterial,
  type StudentAnswer,
} from "@/api/examinations";
import { fetchStudentEnrollments, fetchStudents } from "@/api/students";

interface AnswerDraft {
  text: string;
  score: string;
  notes: string;
}

export function AIMarkingPage() {
  const queryClient = useQueryClient();
  const [sessionId, setSessionId] = useState("");
  const [termId, setTermId] = useState("");
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [assessmentId, setAssessmentId] = useState("");
  const [examinationId, setExaminationId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [scriptId, setScriptId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [drafts, setDrafts] = useState<Record<number, AnswerDraft>>({});
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [scriptUrl, setScriptUrl] = useState("");

  const sessions = useQuery({ queryKey: ["ai-sessions"], queryFn: fetchSessions });
  const terms = useQuery({ queryKey: ["ai-terms", sessionId], queryFn: () => fetchTerms(Number(sessionId)), enabled: Boolean(sessionId) });
  const classes = useQuery({ queryKey: ["ai-classes"], queryFn: fetchClasses });
  const subjects = useQuery({ queryKey: ["ai-subjects"], queryFn: fetchSubjects });
  const classSubjects = useQuery({ queryKey: ["ai-class-subjects", classId], queryFn: () => fetchClassSubjects(Number(classId)), enabled: Boolean(classId) });
  const assessments = useQuery({ queryKey: ["assessment-types"], queryFn: fetchAssessmentTypes });
  const enrollments = useQuery({ queryKey: ["ai-enrollments", sessionId, classId], queryFn: fetchStudentEnrollments, enabled: Boolean(sessionId && classId) });
  const students = useQuery({ queryKey: ["ai-students"], queryFn: fetchStudents });
  const examinations = useQuery({ queryKey: ["examinations"], queryFn: fetchExaminations });

  useEffect(() => {
    if (!sessionId && sessions.data?.length) setSessionId(String(sessions.data.find((item) => item.is_current)?.id ?? sessions.data[0].id));
  }, [sessions.data, sessionId]);
  useEffect(() => {
    if (terms.data?.length && !terms.data.some((term) => String(term.id) === termId)) {
      setTermId(String(terms.data.find((term) => term.is_current)?.id ?? terms.data[0].id));
    }
  }, [terms.data, termId]);
  useEffect(() => {
    if (classes.data?.length && !classes.data.some((item) => String(item.id) === classId)) setClassId(String(classes.data[0].id));
  }, [classes.data, classId]);
  useEffect(() => {
    if (subjectId && !classSubjects.data?.some((link) => String(link.subject_id) === subjectId)) setSubjectId("");
  }, [classSubjects.data, subjectId]);
  useEffect(() => {
    if (assessments.data?.length && !assessments.data.some((item) => String(item.id) === assessmentId)) {
      const standard = assessments.data.find((item) => item.name.toLowerCase() === "ca1");
      if (standard) setAssessmentId(String(standard.id));
    }
  }, [assessments.data, assessmentId]);

  const assignedSubjects = useMemo(() => {
    const linkedIds = new Set((classSubjects.data ?? []).map((link) => link.subject_id));
    return (subjects.data ?? []).filter((item) => linkedIds.has(item.id));
  }, [classSubjects.data, subjects.data]);
  const standardAssessments = useMemo(() => {
    const order = new Map([["ca1", 1], ["ca2", 2], ["ca3", 3], ["exam", 4]]);
    return (assessments.data ?? []).filter((item) => order.has(item.name.toLowerCase())).sort((a, b) => order.get(a.name.toLowerCase())! - order.get(b.name.toLowerCase())!);
  }, [assessments.data]);
  const enrolledStudents = useMemo(() => {
    const ids = new Set((enrollments.data ?? []).filter((item) => item.academic_session_id === Number(sessionId) && item.school_class_id === Number(classId)).map((item) => item.student_id));
    return (students.data ?? []).filter((item) => ids.has(item.id));
  }, [classId, enrollments.data, sessionId, students.data]);
  const matchingExaminations = useMemo(() => (examinations.data ?? []).filter((exam) =>
    exam.academic_session_id === Number(sessionId) && exam.term_id === Number(termId) &&
    exam.school_class_id === Number(classId) && exam.subject_id === Number(subjectId) && exam.status !== "CLOSED"
  ), [classId, examinations.data, sessionId, subjectId, termId]);
  useEffect(() => {
    if (matchingExaminations.length && !matchingExaminations.some((exam) => String(exam.id) === examinationId)) {
      setExaminationId(String(matchingExaminations[0].id));
    }
  }, [examinationId, matchingExaminations]);
  const selectedExam = matchingExaminations.find((exam) => String(exam.id) === examinationId) ?? matchingExaminations[0];
  const scripts = useQuery({ queryKey: ["ai-scripts", selectedExam?.id], queryFn: () => fetchStudentScripts(selectedExam!.id), enabled: Boolean(selectedExam) });
  const selectedScript = (scripts.data ?? []).find((script) => String(script.id) === scriptId) ??
    (scripts.data ?? []).find((script) => script.student_id === Number(studentId) && script.assessment_type_id === Number(assessmentId));
  const questions = useQuery({ queryKey: ["ai-questions", selectedExam?.id], queryFn: () => fetchQuestions(selectedExam!.id), enabled: Boolean(selectedExam) });
  const answers = useQuery({ queryKey: ["ai-answers", selectedScript?.id], queryFn: () => fetchScriptAnswers(selectedScript!.id), enabled: Boolean(selectedScript && ["AI_MARKED", "TEACHER_REVIEW", "APPROVED"].includes(selectedScript.status)) });
  const references = useQuery({
    queryKey: ["ai-references", questions.data?.map((question) => question.id)],
    queryFn: async (): Promise<Record<number, ReferenceMaterial[]>> => Object.fromEntries(await Promise.all((questions.data ?? []).map(async (question) => [question.id, await fetchQuestionReferences(question.id)]))),
    enabled: Boolean(questions.data?.length),
  });
  const selectedAssessment = standardAssessments.find((item) => String(item.id) === assessmentId);
  const selectedStudent = enrolledStudents.find((item) => String(item.id) === studentId);

  useEffect(() => {
    if (!selectedScript) {
      setScriptUrl("");
      return;
    }
    let url = "";
    fetchScriptFile(selectedScript.id).then((blob) => {
      url = URL.createObjectURL(blob);
      setScriptUrl(url);
    }).catch(() => setError("Unable to load the original script file."));
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [selectedScript?.id]);

  const uploadMutation = useMutation({
    mutationFn: () => uploadStudentScript(selectedExam!.id, Number(studentId), Number(assessmentId), file!),
    onSuccess: async (script) => {
      setScriptId(String(script.id));
      setFile(null);
      setError("");
      setNotice("Script uploaded and stored. Start AI marking when ready.");
      await queryClient.invalidateQueries({ queryKey: ["ai-scripts", selectedExam?.id] });
    },
    onError: (reason: any) => setError(reason?.response?.data?.detail ?? "Script upload failed."),
  });
  const processMutation = useMutation({
    mutationFn: () => startScriptMarking(selectedScript!.id),
    onSuccess: async (script) => {
      setNotice(`AI marking finished: ${script.status}. Review every question before approval.`);
      setError("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ai-scripts", selectedExam?.id] }),
        queryClient.invalidateQueries({ queryKey: ["ai-answers", selectedScript?.id] }),
      ]);
    },
    onError: (reason: any) => setError(reason?.response?.data?.detail ?? "AI marking failed."),
  });
  const reviewMutation = useMutation({
    mutationFn: ({ answer, draft }: { answer: StudentAnswer; draft: AnswerDraft }) => reviewScriptAnswer(answer.id, {
      teacher_final_score: Number(draft.score),
      teacher_review_notes: draft.notes || null,
      extracted_text: draft.text,
      review_status: "REVIEWED",
    }),
    onSuccess: async () => {
      setNotice("Teacher review saved.");
      setError("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ai-answers", selectedScript?.id] }),
        queryClient.invalidateQueries({ queryKey: ["ai-scripts", selectedExam?.id] }),
      ]);
    },
    onError: (reason: any) => setError(reason?.response?.data?.detail ?? "Unable to save review."),
  });
  const approveMutation = useMutation({
    mutationFn: () => approveStudentScript(selectedScript!.id, Number(assessmentId)),
    onSuccess: async () => {
      setNotice("Teacher approval recorded. The official score and result have been recalculated.");
      setError("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["ai-scripts", selectedExam?.id] }),
        queryClient.invalidateQueries({ queryKey: ["ai-answers", selectedScript?.id] }),
        queryClient.invalidateQueries({ queryKey: ["score-entries"] }),
        queryClient.invalidateQueries({ queryKey: ["score-results"] }),
        queryClient.invalidateQueries({ queryKey: ["student-results"] }),
        queryClient.invalidateQueries({ queryKey: ["student-scores"] }),
        queryClient.invalidateQueries({ queryKey: ["student-report-card"] }),
      ]);
    },
    onError: (reason: any) => setError(reason?.response?.data?.detail ?? "Approval failed."),
  });

  function draftFor(answer: StudentAnswer): AnswerDraft {
    return drafts[answer.id] ?? {
      text: answer.extracted_text ?? "",
      score: answer.teacher_final_score?.toString() ?? answer.ai_proposed_score?.toString() ?? "",
      notes: answer.teacher_review_notes ?? "",
    };
  }
  function updateDraft(answer: StudentAnswer, update: Partial<AnswerDraft>) {
    setDrafts((current) => ({ ...current, [answer.id]: { ...draftFor(answer), ...update } }));
  }
  function approve() {
    if (!selectedScript || !selectedAssessment || !selectedStudent) return;
    const total = (answers.data ?? []).reduce((sum, answer) => sum + Number(draftFor(answer).score || 0), 0);
    if (window.confirm(`Approve ${selectedAssessment.name} for ${selectedStudent.first_name} ${selectedStudent.last_name} at ${total}/${selectedAssessment.max_score}? This updates the official score and result.`)) {
      approveMutation.mutate();
    }
  }
  async function openReferenceFile(referenceId: number) {
    const preview = window.open("about:blank", "_blank");
    if (!preview) {
      setError("Allow the reference preview window, then try again.");
      return;
    }
    try {
      const blob = await fetchReferenceFile(referenceId);
      const url = URL.createObjectURL(blob);
      preview.location.href = url;
      window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch {
      preview.close();
      setError("Unable to load this reference file.");
    }
  }

  const allReviewed = Boolean(answers.data?.length && answers.data.every((answer) => answer.review_status === "REVIEWED" && answer.teacher_final_score !== null));
  const allChangesSaved = Boolean(answers.data?.every((answer) => {
    const draft = drafts[answer.id];
    return !draft || (draft.text === (answer.extracted_text ?? "") && Number(draft.score) === Number(answer.teacher_final_score) && draft.notes === (answer.teacher_review_notes ?? ""));
  }));
  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-6xl space-y-6">
    <header className="flex flex-wrap items-end justify-between gap-4"><div><Link to="/dashboard" className="text-sm text-slate-500">← Dashboard</Link><p className="mt-4 text-sm font-medium text-slate-500">Teacher assessment workflow</p><h1 className="mt-1 text-3xl font-bold text-slate-900">AI Marking</h1></div><Link to="/examinations" className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm">Manage examinations & questions</Link></header>
    {(notice || error) && <div role={error ? "alert" : "status"} className={`rounded-md border p-3 text-sm ${error ? "border-red-200 bg-red-50 text-red-800" : "border-emerald-200 bg-emerald-50 text-emerald-900"}`}>{error || notice}</div>}

    <section className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-2 lg:grid-cols-3">
      <Select label="Session" value={sessionId} onChange={(value) => { setSessionId(value); setTermId(""); setScriptId(""); setExaminationId(""); }} items={(sessions.data ?? []).map((item) => [String(item.id), item.name])} />
      <Select label="Term" value={termId} onChange={(value) => { setTermId(value); setScriptId(""); setExaminationId(""); }} items={(terms.data ?? []).map((item) => [String(item.id), item.name])} disabled={!sessionId} />
      <Select label="Class" value={classId} onChange={(value) => { setClassId(value); setSubjectId(""); setStudentId(""); setScriptId(""); setExaminationId(""); }} items={(classes.data ?? []).map((item) => [String(item.id), item.name])} />
      <Select label="Subject" value={subjectId} onChange={(value) => { setSubjectId(value); setScriptId(""); setExaminationId(""); }} items={assignedSubjects.map((item) => [String(item.id), item.name])} disabled={!classId} />
      <Select label="Assessment type" value={assessmentId} onChange={(value) => { setAssessmentId(value); setScriptId(""); }} items={standardAssessments.map((item) => [String(item.id), `${item.name} · ${item.max_score} marks`])} />
      <Select label="Student" value={studentId} onChange={(value) => { setStudentId(value); setScriptId(""); }} items={enrolledStudents.map((item) => [String(item.id), `${item.first_name} ${item.last_name} · ${item.admission_number}`])} disabled={!classId || !sessionId} />
      {matchingExaminations.length > 1 && <Select label="Question set" value={selectedExam ? String(selectedExam.id) : examinationId} onChange={setExaminationId} items={matchingExaminations.map((exam) => [String(exam.id), exam.title])} />}
    </section>

    {!selectedExam && sessionId && termId && classId && subjectId && <p className="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">No open examination matches this session, term, class and subject. Create one with questions before uploading scripts.</p>}
    {selectedExam && <>
      <section className="flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <label className="min-w-56 flex-1"><span className="mb-1 block text-sm font-medium text-slate-700">Student script · {selectedAssessment?.name ?? "select assessment"}</span><input type="file" accept=".pdf,.jpg,.jpeg,.png,.txt,application/pdf,image/jpeg,image/png,text/plain" onChange={(event) => setFile(event.target.files?.[0] ?? null)} className="block w-full text-sm" /></label>
        <button type="button" disabled={!selectedStudent || !selectedAssessment || !file || uploadMutation.isPending} onClick={() => uploadMutation.mutate()} className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{uploadMutation.isPending ? "Uploading..." : "Upload script"}</button>
      </section>

      {selectedScript && <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4"><div><p className="font-semibold">{selectedStudent ? `${selectedStudent.first_name} ${selectedStudent.last_name}` : "Selected script"}</p><p className="mt-1 text-sm text-slate-600">{selectedExam.title} · {selectedAssessment?.name} · {selectedScript.original_filename} · {formatBytes(selectedScript.file_size)} · {selectedScript.status}</p>{selectedScript.processing_error && <p className="mt-1 text-sm text-red-700">{selectedScript.processing_error}</p>}</div><div className="flex flex-wrap gap-2"><button type="button" disabled={!scriptUrl} onClick={() => window.open(scriptUrl, "_blank", "noopener,noreferrer")} className="rounded-md border border-slate-300 px-3 py-2 text-sm">View original</button><button type="button" disabled={!['UPLOADED','PROCESSING_FAILED','MARKING_FAILED'].includes(selectedScript.status) || processMutation.isPending} onClick={() => processMutation.mutate()} className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-50">{processMutation.isPending || selectedScript.status === "PROCESSING" ? "Processing..." : "Start AI marking"}</button></div></div>
        {scriptUrl && selectedScript.content_type?.startsWith("image/") && <img src={scriptUrl} alt="Uploaded student script" className="max-h-[70vh] max-w-full rounded border border-slate-200 bg-white object-contain" />}
        {scriptUrl && selectedScript.content_type === "application/pdf" && <iframe src={scriptUrl} title="Uploaded student script" className="h-[70vh] w-full rounded border border-slate-200 bg-white" />}

        {answers.data && <div className="space-y-4"><h2 className="text-xl font-semibold text-slate-900">Question review</h2>{answers.data.map((answer) => {
          const question = questions.data?.find((item) => item.id === answer.question_id);
          const draft = draftFor(answer);
          const locked = selectedScript.status === "APPROVED";
          return <article key={answer.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap justify-between gap-2"><h3 className="font-semibold">{question?.question_number ?? `Question ${answer.question_id}`} · {question?.question_text}</h3><span className="text-sm text-slate-500">Maximum {question?.maximum_marks ?? "?"} · {answer.review_status} · {answer.extraction_status ?? ""}</span></div>
            <label className="mt-4 block"><span className="text-xs font-semibold uppercase text-slate-500">Extracted student answer · edit if needed</span><textarea value={draft.text} onChange={(event) => updateDraft(answer, { text: event.target.value })} disabled={locked} className="mt-1 min-h-20 w-full rounded border border-slate-300 p-2 text-sm" /></label>
            {(references.data?.[answer.question_id] ?? []).map((reference) => (reference.text_content || reference.original_filename) && <div key={reference.id} className="mt-3 rounded bg-slate-50 p-3"><p className="text-xs font-semibold uppercase text-slate-500">{reference.title ?? reference.material_type}</p>{reference.text_content && <p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{reference.text_content}</p>}{reference.original_filename && <button type="button" onClick={() => openReferenceFile(reference.id)} className="mt-2 text-sm font-medium text-sky-800 underline">Open reference file · {reference.original_filename}</button>}</div>)}
            <div className="mt-3 grid gap-3 md:grid-cols-[1fr_10rem]"><div className="rounded bg-slate-50 p-3"><p className="text-xs font-semibold uppercase text-slate-500">AI proposed score: {answer.ai_proposed_score ?? "Needs teacher input"} / {question?.maximum_marks ?? "?"}</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{answer.ai_evidence ?? "No AI evidence returned."}</p>{answer.ai_confidence !== null && <p className="mt-1 text-xs text-slate-500">Extraction/marking confidence: {(answer.ai_confidence * 100).toFixed(0)}%</p>}</div><label><span className="text-xs font-semibold uppercase text-slate-500">Teacher final score</span><input type="number" min="0" max={question?.maximum_marks} step="0.01" value={draft.score} onChange={(event) => updateDraft(answer, { score: event.target.value })} disabled={locked} className="mt-1 w-full rounded border border-slate-300 p-2" /></label></div>
            <label className="mt-3 block"><span className="text-xs font-semibold uppercase text-slate-500">Teacher notes</span><textarea value={draft.notes} onChange={(event) => updateDraft(answer, { notes: event.target.value })} disabled={locked} className="mt-1 min-h-16 w-full rounded border border-slate-300 p-2 text-sm" /></label>
            {!locked && <button type="button" disabled={draft.score === "" || Number(draft.score) > Number(question?.maximum_marks) || Number(draft.score) < 0 || reviewMutation.isPending} onClick={() => reviewMutation.mutate({ answer, draft })} className="mt-3 rounded-md border border-slate-300 px-3 py-2 text-sm disabled:opacity-50">Save teacher review</button>}
          </article>;
        })}
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4"><p className="text-sm text-slate-600">Official score is written only after all answers are reviewed and saved, then explicitly approved.</p><button type="button" disabled={!allReviewed || !allChangesSaved || selectedScript.status === "APPROVED" || approveMutation.isPending} onClick={approve} className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">{selectedScript.status === "APPROVED" ? "Approved" : "Approve final marking"}</button></div>
        </div>}
      </section>}
      {(scripts.data ?? []).length > 0 && <section className="rounded-lg border border-slate-200 bg-white p-4"><h2 className="font-semibold">Scripts for this examination</h2><div className="mt-2 divide-y">{scripts.data?.map((script) => <button type="button" key={script.id} onClick={() => { setScriptId(String(script.id)); setStudentId(String(script.student_id)); setAssessmentId(String(script.assessment_type_id ?? "")); }} className={`flex w-full justify-between gap-3 py-2 text-left text-sm ${selectedScript?.id === script.id ? "font-semibold text-slate-900" : "text-slate-600"}`}><span>{enrolledStudents.find((item) => item.id === script.student_id)?.first_name ?? `Student #${script.student_id}`} · {standardAssessments.find((item) => item.id === script.assessment_type_id)?.name ?? "Assessment not set"} · {script.original_filename}</span><span>{script.status}</span></button>)}</div></section>}
    </>}
  </div></main>;
}

function Select({ label, value, onChange, items, disabled = false }: { label: string; value: string; onChange: (value: string) => void; items: [string, string][]; disabled?: boolean }) {
  return <label className="block"><span className="mb-1 block text-sm font-medium text-slate-700">{label}</span><select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)} className="w-full rounded border border-slate-300 bg-white p-2 text-sm disabled:bg-slate-100"><option value="">Select {label.toLowerCase()}</option>{items.map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select></label>;
}

function formatBytes(size: number | null) {
  if (size === null) return "size unknown";
  if (size < 1024) return `${size} B`;
  return `${(size / 1024 / 1024).toFixed(1)} MB`;
}
