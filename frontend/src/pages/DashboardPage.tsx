import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMySchool } from "@/api/schools";
import { fetchAssessmentTypes, fetchClasses, fetchSessions, fetchTeacherAssignments } from "@/api/academic";
import { fetchStudentEnrollments, fetchStudents } from "@/api/students";
import { fetchExaminations, fetchStudentScripts } from "@/api/examinations";
import { useAuth } from "@/context/AuthContext";
import { roleLabel } from "@/utils/roleLabels";
import { MetricTile, PageHeading, StatusBadge } from "@/components/AcademicUI";

export function DashboardPage() {
  const { user } = useAuth();
  const schoolQuery = useQuery({ queryKey: ["my-school"], queryFn: fetchMySchool, enabled: Boolean(user?.school_id) && user?.role !== "STUDENT" });
  const assignments = useQuery({ queryKey: ["teacher-assignments"], queryFn: fetchTeacherAssignments, enabled: user?.role === "TEACHER" });
  const studentProfile = useQuery({ queryKey: ["students"], queryFn: fetchStudents, enabled: user?.role === "STUDENT" });
  const studentEnrollments = useQuery({ queryKey: ["student-enrollments"], queryFn: fetchStudentEnrollments, enabled: user?.role === "STUDENT" });
  const classes = useQuery({ queryKey: ["classes"], queryFn: fetchClasses, enabled: user?.role === "STUDENT" });
  const sessions = useQuery({ queryKey: ["dashboard-sessions"], queryFn: fetchSessions, enabled: user?.role !== "STUDENT" });
  const allClasses = useQuery({ queryKey: ["classes"], queryFn: fetchClasses, enabled: user?.role !== "STUDENT" });
  const allStudents = useQuery({ queryKey: ["students"], queryFn: fetchStudents, enabled: user?.role !== "STUDENT" });
  const exams = useQuery({ queryKey: ["examinations"], queryFn: fetchExaminations, enabled: user?.role !== "STUDENT" });
  const assessmentTypes = useQuery({ queryKey: ["assessment-types"], queryFn: fetchAssessmentTypes, enabled: user?.role !== "STUDENT" });
  const aiQueue = useQuery({
    queryKey: ["dashboard-ai-queue", exams.data?.map((exam) => exam.id)],
    enabled: Boolean(exams.data?.length) && user?.role !== "STUDENT",
    queryFn: async () => {
      const scriptGroups = await Promise.all((exams.data ?? []).map(async (exam) => ({
        exam,
        scripts: await fetchStudentScripts(exam.id),
      })));
      return scriptGroups.flatMap(({ exam, scripts }) => scripts
        .filter((script) => ["AI_MARKED", "TEACHER_REVIEW"].includes(script.status))
        .map((script) => ({ exam, script })));
    },
  });

  if (user?.role === "STUDENT") {
    const student = studentProfile.data?.[0];
    const currentClass = classes.data?.find((item) => item.id === studentEnrollments.data?.[0]?.school_class_id);
    return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-5xl space-y-5">
      <PageHeading eyebrow="STUDENT RECORD" title={student ? `${student.first_name} ${student.last_name}` : "Student dashboard"} description={`${student?.admission_number ?? "Admission number pending"} · ${currentClass?.name ?? "Class not assigned"}`} />
      <section className="academic-student-home">
        <div className="academic-student-home-icon"><span className="material-symbols-outlined" aria-hidden="true">school</span></div>
        <div><p className="academic-eyebrow">MY ACADEMIC RECORD</p><h2>Results and report card</h2><p>Review your approved assessment scores, subject totals, grades and class standing.</p></div>
        <Link to="/student/results" className="academic-primary-action"><span className="material-symbols-outlined" aria-hidden="true">workspace_premium</span>View my results</Link>
      </section>
    </div></main>;
  }

  const teacher = user?.role === "TEACHER";
  const classCount = teacher ? new Set((assignments.data ?? []).map((item) => item.school_class_id)).size : (allClasses.data ?? []).length;
  const subjectCount = teacher ? (assignments.data ?? []).length : (allClasses.data ?? []).length;
  const studentCount = (allStudents.data ?? []).length;
  const queue = aiQueue.data ?? [];
  const links = teacher
    ? [
        ["Manual score entry", "/scores", "edit_note", "Record CA1, CA2, CA3 and Exam marks."],
        ["AI marking", "/ai-marking", "auto_awesome", "Upload scripts, review proposals and approve scores."],
        ["Examinations", "/examinations", "quiz", "Build question sets and optional marking guidance."],
        ["Students", "/students", "groups", "View students enrolled in your assigned classes."],
      ] as const
    : [
        ["Academic structure", "/academic/sessions", "calendar_month", "Sessions, terms, classes and subjects."],
        ["Teachers & assignments", "/teachers", "co_present", "Assign teachers by class and subject."],
        ["Students", "/students", "groups", "Manage school student records and class enrollment."],
        ["AI marking", "/ai-marking", "auto_awesome", "Review marking proposals and record approved scores."],
        ["Examinations", "/examinations", "quiz", "Manage examinations, questions and scripts."],
        ...(user?.role === "SCHOOL_ADMIN" ? [["School profile", "/school/profile", "domain", "Manage school information and branding."]] as const : []),
      ];

  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-7xl space-y-5">
    <PageHeading eyebrow={teacher ? "TEACHER ACADEMIC DESK" : "SCHOOL_CA · ACADEMIC MANAGEMENT"} title={teacher ? "Academic workspace" : schoolQuery.data?.name ?? roleLabel(user?.role ?? "SCHOOL_ADMIN")} description={teacher ? `${assignments.data?.length ?? 0} active Teacher + Class + Subject assignments` : user?.email ?? "Manage academic records, assessments and results."} />
    <div className="academic-metric-grid">
      <MetricTile label={teacher ? "Assigned class arms" : "Academic sessions"} value={teacher ? classCount : (sessions.data ?? []).length} detail="Available in your workspace" icon={teacher ? "meeting_room" : "calendar_month"} />
      <MetricTile label={teacher ? "Class + subject assignments" : "Classes"} value={teacher ? subjectCount : classCount} detail={teacher ? "Assignment-scoped access" : "Across your school"} icon={teacher ? "assignment_ind" : "domain"} />
      <MetricTile label="Students visible" value={studentCount} detail={teacher ? "Shared class enrollment" : "School records"} icon="groups" tone="green" />
      <MetricTile label="Pending AI reviews" value={queue.length} detail="Awaiting teacher approval" icon="auto_awesome" tone={queue.length ? "amber" : "green"} />
    </div>

    {queue.length > 0 && <section className="academic-surface-panel">
      <div className="academic-section-heading"><div><h2>Scripts pending verification</h2><p>AI proposals remain provisional until a teacher approves them.</p></div><StatusBadge tone="warning">{queue.length} awaiting review</StatusBadge></div>
      <div className="academic-queue-list">{queue.slice(0, 4).map(({ exam, script }) => <div className="academic-queue-row" key={script.id}>
        <div className="academic-queue-initials" aria-hidden="true">{(allStudents.data ?? []).find((item) => item.id === script.student_id)?.first_name?.[0] ?? "S"}</div>
        <div className="academic-queue-copy"><strong>{(allStudents.data ?? []).find((item) => item.id === script.student_id)?.first_name ?? `Student #${script.student_id}`} · {exam.title}</strong><span>{exam.school_class_id ? `Class #${exam.school_class_id}` : "Class"} · {assessmentTypes.data?.find((item) => item.id === script.assessment_type_id)?.name ?? "Assessment not selected"}</span></div>
        <StatusBadge tone="warning">{script.status === "TEACHER_REVIEW" ? "Teacher review" : "AI marked"}</StatusBadge>
        <Link to="/ai-marking" className="academic-small-action">Review<span className="material-symbols-outlined" aria-hidden="true">arrow_forward</span></Link>
      </div>)}</div>
    </section>}

    <section>
      <div className="academic-section-heading"><div><h2>Quick actions</h2><p>Continue with the academic task you need.</p></div></div>
      <div className="academic-quick-grid">{links.map(([label, path, icon, description]) => <Link key={path} to={path} className="academic-quick-link">
        <span className="academic-quick-icon"><span className="material-symbols-outlined" aria-hidden="true">{icon}</span></span>
        <span><strong>{label}</strong><small>{description}</small></span>
      </Link>)}</div>
    </section>
    <div className="academic-notice"><span className="material-symbols-outlined" aria-hidden="true">policy</span><div><strong>Assessment integrity</strong><br />AI proposals require explicit teacher review and approval before entering the normal score and result records.</div></div>
  </div></main>;
}
