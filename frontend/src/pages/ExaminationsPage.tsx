import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createExamination, createQuestion, createReference, fetchExaminations, fetchQuestions, uploadQuestionPaper, uploadReference, uploadStudentScript, type ExaminationQuestion, type QuestionType } from "@/api/examinations";
import { fetchAssessmentTypes, fetchClasses, fetchSessions, fetchSubjects, fetchTerms } from "@/api/academic";
import { useAuth } from "@/context/AuthContext";

export function ExaminationsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<number>();
  const [termId, setTermId] = useState<number>();
  const [classId, setClassId] = useState<number>();
  const [subjectId, setSubjectId] = useState<number>();
  const [title, setTitle] = useState("");
  const [questionNumber, setQuestionNumber] = useState("1");
  const [questionText, setQuestionText] = useState("");
  const [questionType, setQuestionType] = useState<QuestionType>("SUBJECTIVE");
  const [maximumMarks, setMaximumMarks] = useState("1");
  const [correctOption, setCorrectOption] = useState("");
  const [markingGuidance, setMarkingGuidance] = useState("");
  const [referenceAnswer, setReferenceAnswer] = useState("");
  const [paper, setPaper] = useState<File | null>(null);
  const [referenceFile, setReferenceFile] = useState<File | null>(null);
  const [studentId, setStudentId] = useState("");
  const [assessmentTypeId, setAssessmentTypeId] = useState("");
  const [scriptFile, setScriptFile] = useState<File | null>(null);
  const [message, setMessage] = useState("");

  const exams = useQuery({ queryKey: ["examinations"], queryFn: fetchExaminations });
  const sessions = useQuery({ queryKey: ["exam-sessions"], queryFn: fetchSessions });
  const classes = useQuery({ queryKey: ["exam-classes"], queryFn: fetchClasses });
  const subjects = useQuery({ queryKey: ["exam-subjects"], queryFn: fetchSubjects });
  const assessmentTypes = useQuery({ queryKey: ["assessment-types"], queryFn: fetchAssessmentTypes });
  const terms = useQuery({ queryKey: ["exam-terms", sessionId], queryFn: () => fetchTerms(sessionId!), enabled: Boolean(sessionId) });
  const questions = useQuery({ queryKey: ["exam-questions", selectedId], queryFn: () => fetchQuestions(selectedId!), enabled: Boolean(selectedId) });

  useEffect(() => {
    if (!sessionId && sessions.data?.[0]) setSessionId(sessions.data[0].id);
    if (!classId && classes.data?.[0]) setClassId(classes.data[0].id);
    if (!subjectId && subjects.data?.[0]) setSubjectId(subjects.data[0].id);
  }, [sessions.data, classes.data, subjects.data, sessionId, classId, subjectId]);
  useEffect(() => { if (terms.data?.[0]) setTermId(terms.data[0].id); }, [terms.data]);

  const createExam = useMutation({
    mutationFn: () => createExamination({ academic_session_id: sessionId!, term_id: termId!, school_class_id: classId!, subject_id: subjectId!, title, maximum_score: 70 }),
    onSuccess: (exam) => { setTitle(""); setSelectedId(exam.id); setMessage("Examination created."); queryClient.invalidateQueries({ queryKey: ["examinations"] }); },
    onError: (error: any) => setMessage(error?.response?.data?.detail ?? "Unable to create examination."),
  });
  const addQuestion = useMutation({
    mutationFn: () => createQuestion(selectedId!, { question_number: questionNumber, section: null, question_text: questionText, question_type: questionType, maximum_marks: Number(maximumMarks), display_order: Number(questionNumber), instructions: null, correct_option: questionType === "OBJECTIVE" ? correctOption : null, expected_concepts: null, key_points: null, acceptable_alternatives: null, partial_credit_guidance: null, marking_guidance: markingGuidance || null, teacher_notes: null }),
    onSuccess: () => { setQuestionText(""); setMarkingGuidance(""); setCorrectOption(""); setMessage("Question added."); queryClient.invalidateQueries({ queryKey: ["exam-questions", selectedId] }); },
    onError: (error: any) => setMessage(error?.response?.data?.detail ?? "Unable to add question."),
  });
  const addReference = useMutation({
    mutationFn: () => createQuestionReference(),
    onSuccess: () => { setReferenceAnswer(""); setMessage("Reference answer saved."); },
    onError: (error: any) => setMessage(error?.response?.data?.detail ?? "Unable to save reference answer."),
  });
  async function createQuestionReference() {
    const currentQuestion = questions.data?.[questions.data.length - 1];
    if (!currentQuestion) throw new Error("Add a question first.");
    return createReference(currentQuestion.id, { material_type: "TYPED_ANSWER", title: "Teacher reference answer", text_content: referenceAnswer });
  }
  const referenceUploadMutation = useMutation({
    mutationFn: async () => {
      const currentQuestion = questions.data?.[questions.data.length - 1];
      if (!currentQuestion || !referenceFile) throw new Error("Add a question and choose a reference file first.");
      return uploadReference(currentQuestion.id, referenceFile, "HANDWRITTEN", referenceFile.name);
    },
    onSuccess: () => { setReferenceFile(null); setMessage("Original reference file preserved."); },
  });
  const scriptMutation = useMutation({
    mutationFn: () => uploadStudentScript(selectedId!, Number(studentId), Number(assessmentTypeId), scriptFile!),
    onSuccess: () => { setStudentId(""); setScriptFile(null); setMessage("Student script uploaded and preserved."); },
  });
  const paperMutation = useMutation({ mutationFn: () => uploadQuestionPaper(selectedId!, paper!), onSuccess: () => { setPaper(null); setMessage("Question paper uploaded and preserved."); } });

  if (!user || !["TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"].includes(user.role)) return null;

  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-6xl space-y-6">
    <div className="flex items-center justify-between"><div><Link to="/dashboard" className="text-sm text-slate-500">← Dashboard</Link><h1 className="mt-1 text-3xl font-bold text-slate-900">Examinations</h1><p className="mt-1 text-sm text-slate-500">Build question papers, marking guidance and script infrastructure.</p></div></div>
    {message && <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm">{message}</div>}
    <section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Create examination</h2><div className="mt-4 grid gap-3 md:grid-cols-5">
      <select className="rounded border p-2" value={sessionId ?? ""} onChange={e => setSessionId(Number(e.target.value))}><option value="">Session</option>{sessions.data?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
      <select className="rounded border p-2" value={termId ?? ""} onChange={e => setTermId(Number(e.target.value))}><option value="">Term</option>{terms.data?.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select>
      <select className="rounded border p-2" value={classId ?? ""} onChange={e => setClassId(Number(e.target.value))}><option value="">Class</option>{classes.data?.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
      <select className="rounded border p-2" value={subjectId ?? ""} onChange={e => setSubjectId(Number(e.target.value))}><option value="">Subject</option>{subjects.data?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select>
      <input className="rounded border p-2" placeholder="Examination title" value={title} onChange={e => setTitle(e.target.value)} />
    </div><button disabled={!title || !sessionId || !termId || !classId || !subjectId || createExam.isPending} onClick={() => createExam.mutate()} className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50">Create</button></section>
    <section className="grid gap-6 lg:grid-cols-3"><div className="rounded-xl border border-slate-200 bg-white p-5 lg:col-span-1"><h2 className="font-semibold">Your examinations</h2><div className="mt-3 space-y-2">{exams.data?.map(exam => <button key={exam.id} onClick={() => setSelectedId(exam.id)} className={`block w-full rounded-lg border p-3 text-left ${selectedId === exam.id ? "border-slate-900" : "border-slate-200"}`}><p className="font-medium">{exam.title}</p><p className="text-xs text-slate-500">{exam.maximum_score} marks · {exam.status}</p></button>)}</div></div>
      <div className="space-y-6 lg:col-span-2">{selectedId ? <><section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Add question</h2><div className="mt-4 grid gap-3 md:grid-cols-4"><input className="rounded border p-2" placeholder="Question no." value={questionNumber} onChange={e => setQuestionNumber(e.target.value)} /><select className="rounded border p-2" value={questionType} onChange={e => setQuestionType(e.target.value as QuestionType)}><option value="SUBJECTIVE">Subjective</option><option value="OBJECTIVE">Objective</option></select><input className="rounded border p-2" type="number" min="0.5" step="0.5" value={maximumMarks} onChange={e => setMaximumMarks(e.target.value)} /><input className="rounded border p-2" placeholder="Correct option (A/B/C/D or True/False)" value={correctOption} onChange={e => setCorrectOption(e.target.value)} disabled={questionType !== "OBJECTIVE"} /></div><textarea className="mt-3 min-h-24 w-full rounded border p-2" placeholder="Question text" value={questionText} onChange={e => setQuestionText(e.target.value)} /><textarea className="mt-3 min-h-20 w-full rounded border p-2" placeholder="Marking guidance / partial-credit guidance" value={markingGuidance} onChange={e => setMarkingGuidance(e.target.value)} /><button disabled={!questionText || addQuestion.isPending} onClick={() => addQuestion.mutate()} className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm text-white disabled:opacity-50">Add question</button></section>
      <section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Questions</h2><div className="mt-3 space-y-3">{questions.data?.map((q: ExaminationQuestion) => <div key={q.id} className="rounded-lg border border-slate-200 p-3"><div className="flex justify-between"><span className="font-medium">{q.question_number}. {q.question_text}</span><span className="text-xs text-slate-500">{q.maximum_marks} marks · {q.question_type}</span></div>{q.marking_guidance && <p className="mt-2 text-sm text-slate-600">Guidance: {q.marking_guidance}</p>}</div>)}</div><textarea className="mt-4 min-h-20 w-full rounded border p-2" placeholder="Typed ideal/reference answer for the latest question" value={referenceAnswer} onChange={e => setReferenceAnswer(e.target.value)} /><button disabled={!referenceAnswer || addReference.isPending} onClick={() => addReference.mutate()} className="mt-2 rounded-lg border border-slate-300 px-4 py-2 text-sm">Save typed reference</button><div className="mt-4 border-t pt-4"><p className="text-sm font-medium">Handwritten / scanned reference</p><input className="mt-2 block text-sm" type="file" accept=".pdf,image/*" onChange={e => setReferenceFile(e.target.files?.[0] ?? null)} /><button disabled={!referenceFile || referenceUploadMutation.isPending} onClick={() => referenceUploadMutation.mutate()} className="mt-2 rounded-lg border border-slate-300 px-4 py-2 text-sm">Upload original reference</button></div></section>
      <section className="rounded-xl border border-slate-200 bg-white p-5"><h2 className="font-semibold">Question paper</h2><p className="mt-1 text-sm text-slate-500">Original uploaded files are preserved for vision/OCR marking.</p><input className="mt-3 block text-sm" type="file" accept=".pdf,image/jpeg,image/png" onChange={e => setPaper(e.target.files?.[0] ?? null)} /><button disabled={!paper || paperMutation.isPending} onClick={() => paperMutation.mutate()} className="mt-3 rounded-lg border border-slate-300 px-4 py-2 text-sm">Upload question paper</button><div className="mt-5 border-t pt-4"><h3 className="font-medium">Student examination script</h3><div className="mt-2 grid gap-2 sm:grid-cols-2"><input className="rounded border p-2 text-sm" type="number" min="1" placeholder="Student ID" value={studentId} onChange={e => setStudentId(e.target.value)} /><select className="rounded border p-2 text-sm" value={assessmentTypeId} onChange={e => setAssessmentTypeId(e.target.value)}><option value="">Select assessment type</option>{assessmentTypes.data?.map(item => <option key={item.id} value={item.id}>{item.name} · {item.max_score}</option>)}</select><input className="text-sm sm:col-span-2" type="file" accept=".pdf,image/jpeg,image/png,text/plain" onChange={e => setScriptFile(e.target.files?.[0] ?? null)} /></div><button disabled={!studentId || !assessmentTypeId || !scriptFile || scriptMutation.isPending} onClick={() => scriptMutation.mutate()} className="mt-2 rounded-lg border border-slate-300 px-4 py-2 text-sm">Upload student script</button></div></section></> : <div className="rounded-xl border border-dashed border-slate-300 bg-white p-8 text-sm text-slate-500">Select an examination to manage its questions and paper.</div>}</div>
    </section>
  </div></main>;
}
