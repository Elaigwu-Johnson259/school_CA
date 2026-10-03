import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchAssessmentTypes, fetchClasses, fetchReportCard, fetchResults, fetchScores, fetchSessions, fetchTerms, fetchSubjects } from "@/api/academic";
import { fetchStudentEnrollments, fetchStudents } from "@/api/students";
import { fetchMySchool, fetchMySchoolLogo } from "@/api/schools";
import { useAuth } from "@/context/AuthContext";

export function StudentResultPage() {
  const { logout } = useAuth();
  const [termId, setTermId] = useState("");
  const [schoolLogo, setSchoolLogo] = useState("");
  const school = useQuery({ queryKey: ["my-school"], queryFn: fetchMySchool });
  const sessions = useQuery({ queryKey: ["sessions"], queryFn: fetchSessions });
  const currentSession = sessions.data?.find((item) => item.is_current) ?? sessions.data?.[0];
  const terms = useQuery({ queryKey: ["student-terms", currentSession?.id], queryFn: () => fetchTerms(currentSession!.id), enabled: Boolean(currentSession) });
  const selectedTerm = termId || String(terms.data?.find((item) => item.is_current)?.id ?? terms.data?.[0]?.id ?? "");
  const students = useQuery({ queryKey: ["students"], queryFn: fetchStudents });
  const enrollments = useQuery({ queryKey: ["student-enrollments"], queryFn: fetchStudentEnrollments });
  const classes = useQuery({ queryKey: ["classes"], queryFn: fetchClasses });
  const student = students.data?.[0];
  const enrollment = enrollments.data?.find((item) => item.academic_session_id === currentSession?.id);
  const currentClass = classes.data?.find((item) => item.id === enrollment?.school_class_id);
  const results = useQuery({ queryKey: ["student-results", student?.id, selectedTerm], queryFn: () => fetchResults({ student_id: student!.id, term_id: Number(selectedTerm) }), enabled: Boolean(student && selectedTerm) });
  const reportCard = useQuery({ queryKey: ["student-report-card", student?.id, selectedTerm], queryFn: () => fetchReportCard(student!.id, Number(selectedTerm)), enabled: Boolean(student && selectedTerm) });
  const scores = useQuery({ queryKey: ["student-scores", student?.id, selectedTerm], queryFn: () => fetchScores({ student_id: student!.id, term_id: Number(selectedTerm) }), enabled: Boolean(student && selectedTerm) });
  const assessments = useQuery({ queryKey: ["assessment-types"], queryFn: fetchAssessmentTypes });
  const subjects = useQuery({ queryKey: ["subjects"], queryFn: fetchSubjects });
  const subjectMap = new Map((subjects.data ?? []).map((item) => [item.id, item.name]));
  const scoreMap = useMemo(() => { const map = new Map<string, number>(); for (const score of scores.data ?? []) map.set(`${score.subject_id}:${score.assessment_type_id}`, score.value); return map; }, [scores.data]);
  const totalMax = (results.data ?? []).length * 100;
  const total = (results.data ?? []).reduce((sum, item) => sum + Number(item.total), 0);
  const average = results.data?.length ? total / results.data.length : 0;

  useEffect(() => {
    let objectUrl = "";
    if (school.data?.logo_path) {
      fetchMySchoolLogo().then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setSchoolLogo(objectUrl);
      }).catch(() => setSchoolLogo(""));
    } else {
      setSchoolLogo("");
    }
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [school.data?.logo_path]);

  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-7xl space-y-6">
    <header className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><div className="flex flex-wrap items-start justify-between gap-4"><div className="flex items-center gap-4">{schoolLogo && <img src={schoolLogo} alt={`${school.data?.name ?? "School"} logo`} className="h-16 max-w-32 object-contain" />}<div><p className="text-sm font-semibold" style={{ color: school.data?.primary_color ?? "#334155" }}>{school.data?.name ?? "School"}</p><p className="text-xs text-slate-500">{[school.data?.address, school.data?.phone, school.data?.email].filter(Boolean).join(" · ")}</p>{school.data?.motto && <p className="mt-1 text-xs italic text-slate-500">{school.data.motto}</p>}</div></div><button onClick={() => logout()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">Log out</button><div className="w-full border-t border-slate-200 pt-4"><Link to="/dashboard" className="text-sm font-medium text-slate-600 hover:text-slate-900">← Back to Dashboard</Link><p className="mt-3 text-sm text-slate-500">Student Result</p><h1 className="mt-1 text-2xl font-bold text-slate-900">{student ? `${student.first_name} ${student.last_name}` : "Your Result"}</h1><p className="mt-1 text-sm text-slate-500">{student?.admission_number} · {currentClass?.name ?? "Class not assigned"} · {currentSession?.name ?? ""}</p></div></div></header>
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><label className="block max-w-xs"><span className="text-sm font-medium text-slate-700">Term</span><select value={selectedTerm} onChange={(e) => setTermId(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2">{(terms.data ?? []).map((term) => <option key={term.id} value={term.id}>{term.name}</option>)}</select></label></section>
    <section className="grid gap-4 md:grid-cols-4"><Summary label="Overall Aggregate" value={`${total} / ${totalMax}`} /><Summary label="Average" value={`${average.toFixed(2)}%`} /><Summary label="Overall Class Position" value={reportCard.data?.class_position ? ordinal(reportCard.data.class_position) : "—"} /><Summary label="Subjects" value={String(results.data?.length ?? 0)} /><Summary label="Academic Session" value={currentSession?.name ?? "—"} /></section>
    <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm"><div className="border-b border-slate-200 p-5"><h2 className="font-semibold text-slate-900">Complete Result</h2><p className="mt-1 text-sm text-slate-500">Assessment breakdown and calculated result. Scores are read-only.</p></div><div className="overflow-x-auto"><table className="min-w-full divide-y divide-slate-200"><thead className="bg-slate-50"><tr>{["Subject","CA1","CA2","CA3","CA Total","Exam","Total","Grade","Position"].map((h) => <th key={h} className="px-4 py-3 text-left text-xs font-semibold uppercase text-slate-500">{h}</th>)}</tr></thead><tbody className="divide-y divide-slate-100">{(results.data ?? []).map((result) => { const caTypes=(assessments.data ?? []).filter((a)=>a.category==='CA'); const examTypes=(assessments.data ?? []).filter((a)=>a.category==='EXAM'); const caValues=caTypes.map((a)=>scoreMap.get(`${result.subject_id}:${a.id}`) ?? 0); const exam=examTypes.reduce((sum,a)=>sum+(scoreMap.get(`${result.subject_id}:${a.id}`) ?? 0),0); return <tr key={result.id}><td className="px-4 py-3 text-sm font-semibold text-slate-900">{subjectMap.get(result.subject_id) ?? `Subject #${result.subject_id}`}</td>{caValues.slice(0,3).map((v,i)=><td key={i} className="px-4 py-3 text-sm">{v}/10</td>)}<td className="px-4 py-3 text-sm">{result.ca_total}/30</td><td className="px-4 py-3 text-sm">{exam}/70</td><td className="px-4 py-3 text-sm font-semibold">{result.total}/100</td><td className="px-4 py-3 text-sm font-semibold">{result.grade ?? '—'}</td><td className="px-4 py-3 text-sm font-semibold">{result.subject_position ? ordinal(result.subject_position) : '—'}</td></tr>})}</tbody></table></div>{results.data?.length===0 && <p className="p-6 text-sm text-slate-500">No published/calculated results are available for this term yet.</p>}</section>
  </div></main>;
}

function Summary({label,value}:{label:string;value:string}) { return <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"><p className="text-xs font-semibold uppercase text-slate-500">{label}</p><p className="mt-2 text-xl font-bold text-slate-900">{value}</p></div>; }
function ordinal(value:number){const m=value%100;if(m>=11&&m<=13)return `${value}th`;switch(value%10){case 1:return `${value}st`;case 2:return `${value}nd`;case 3:return `${value}rd`;default:return `${value}th`;}}
