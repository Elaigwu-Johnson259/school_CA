import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMySchool } from "@/api/schools";
import { fetchClasses, fetchTeacherAssignments } from "@/api/academic";
import { fetchStudentEnrollments, fetchStudents } from "@/api/students";
import { useAuth } from "@/context/AuthContext";
import { roleLabel } from "@/utils/roleLabels";

export function DashboardPage() {
  const { user, logout } = useAuth();
  const schoolQuery = useQuery({ queryKey: ["my-school"], queryFn: fetchMySchool, enabled: Boolean(user?.school_id) && user?.role !== "STUDENT" });
  const assignments = useQuery({ queryKey: ["teacher-assignments"], queryFn: fetchTeacherAssignments, enabled: user?.role === "TEACHER" });
  const studentProfile = useQuery({ queryKey: ["students"], queryFn: fetchStudents, enabled: user?.role === "STUDENT" });
  const studentEnrollments = useQuery({ queryKey: ["student-enrollments"], queryFn: fetchStudentEnrollments, enabled: user?.role === "STUDENT" });
  const classes = useQuery({ queryKey: ["classes"], queryFn: fetchClasses, enabled: user?.role === "STUDENT" });

  if (user?.role === "STUDENT") {
    const student = studentProfile.data?.[0];
    const currentClass = classes.data?.find((item) => item.id === studentEnrollments.data?.[0]?.school_class_id);
    return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-5xl space-y-6"><header className="rounded-2xl bg-white border border-slate-200 p-7 shadow-sm"><p className="text-sm text-slate-500">Student Dashboard</p><h1 className="mt-1 text-3xl font-bold text-slate-900">{student ? `${student.first_name} ${student.last_name}` : "Student"}</h1><div className="mt-3 grid gap-2 text-sm text-slate-500 md:grid-cols-3"><span>Admission: {student?.admission_number ?? "—"}</span><span>Class: {currentClass?.name ?? "—"}</span><span>Role: Student</span></div></header><Link to="/student/results" className="block rounded-xl border-2 border-slate-900 bg-white p-7 shadow-sm hover:bg-slate-50"><p className="font-semibold text-slate-900">View My Result</p><p className="mt-2 text-sm text-slate-500">Open your complete CA, exam, grade and position result.</p></Link><button onClick={() => logout()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">Log out</button></div></main>;
  }

  if (user?.role === "TEACHER") {
    return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-6xl space-y-6"><header className="rounded-2xl bg-slate-900 p-7 text-white shadow-sm"><p className="text-sm text-slate-300">Teacher Dashboard</p><h1 className="mt-1 text-3xl font-bold">Academic Work</h1><p className="mt-2 text-slate-300">{assignments.data?.length ?? 0} teaching assignments</p></header><div className="grid gap-4 md:grid-cols-2"><Link to="/scores" className="rounded-xl border-2 border-slate-900 bg-white p-7 shadow-sm"><p className="font-semibold">Enter Scores</p><p className="mt-2 text-sm text-slate-500">CA1, CA2, CA3 and Exam</p></Link><Link to="/students" className="rounded-xl border border-slate-200 bg-white p-7 shadow-sm"><p className="font-semibold">Manage Students</p><p className="mt-2 text-sm text-slate-500">Manage permitted enrollment.</p></Link></div><button onClick={() => logout()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">Log out</button></div></main>;
  }

  return <main className="min-h-screen bg-slate-50 flex items-center justify-center px-4"><div className="w-full max-w-3xl rounded-2xl bg-white border border-slate-200 p-7 shadow-sm"><div className="flex items-start justify-between"><div><p className="text-sm text-slate-500">{roleLabel(user?.role ?? "SCHOOL_ADMIN")}</p><h1 className="mt-1 text-2xl font-bold text-slate-900">{schoolQuery.data?.name ?? "School Results Management"}</h1><p className="mt-2 text-sm text-slate-500">{user?.email}</p></div><button onClick={() => logout()} className="rounded-lg border border-slate-300 px-4 py-2 text-sm">Log out</button></div><div className="mt-7 grid gap-3 md:grid-cols-2"><Link to="/school/profile" className="rounded-lg border border-slate-200 p-4 font-medium">School profile</Link><Link to="/academic/sessions" className="rounded-lg border border-slate-200 p-4 font-medium">Academic sessions & terms</Link><Link to="/students" className="rounded-lg border border-slate-200 p-4 font-medium">Students</Link><Link to="/teachers" className="rounded-lg border border-slate-200 p-4 font-medium">Teachers & assignments</Link></div></div></main>;
}
