import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createTeacher, createTeacherAssignment, fetchClasses, fetchSubjects, fetchTeachers } from "@/api/academic";

export function TeachersPage() {
  const queryClient = useQueryClient();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [classId, setClassId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [teacherId, setTeacherId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const teachers = useQuery({ queryKey: ["teachers"], queryFn: fetchTeachers });
  const classes = useQuery({ queryKey: ["classes"], queryFn: fetchClasses });
  const subjects = useQuery({ queryKey: ["subjects"], queryFn: fetchSubjects });
  const createMutation = useMutation({ mutationFn: () => createTeacher({ first_name: firstName.trim(), last_name: lastName.trim(), email: email.trim() || undefined, password: password || undefined }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["teachers"] }); setFirstName(""); setLastName(""); setEmail(""); setPassword(""); setMessage("Teacher created successfully."); setError(""); } , onError: (e: Error) => { setError(e.message); setMessage(""); }});
  const assignMutation = useMutation({ mutationFn: () => createTeacherAssignment({ teacher_id: Number(teacherId), school_class_id: Number(classId), subject_id: Number(subjectId) }), onSuccess: () => { setMessage("Teacher assignment created."); setError(""); }, onError: (e: Error) => { setError(e.message); setMessage(""); }});
  return <main className="min-h-screen bg-slate-50 px-4 py-8"><div className="mx-auto max-w-6xl space-y-6"><header><Link to="/dashboard" className="text-sm font-medium text-slate-600">← Back to Dashboard</Link><h1 className="mt-4 text-3xl font-bold text-slate-900">Teachers</h1><p className="mt-2 text-slate-600">Create teacher portal accounts and assign classes and subjects.</p></header>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-semibold">Create teacher</h2><div className="mt-5 grid gap-4 md:grid-cols-4"><Input label="First name" value={firstName} setValue={setFirstName}/><Input label="Last name" value={lastName} setValue={setLastName}/><Input label="Email" value={email} setValue={setEmail} type="email"/><Input label="Portal password" value={password} setValue={setPassword} type="password" placeholder="Optional"/></div><button onClick={()=>createMutation.mutate()} disabled={createMutation.isPending || !firstName || !lastName || Boolean(password && password.length<8)} className="mt-5 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50">{createMutation.isPending?"Creating...":"Create Teacher"}</button></section>
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-semibold">Assign teacher</h2><div className="mt-5 grid gap-4 md:grid-cols-3"><Select label="Teacher" value={teacherId} onChange={setTeacherId} options={(teachers.data??[]).map(t=>[t.id,`${t.first_name} ${t.last_name}`] as [number,string])}/><Select label="Class" value={classId} onChange={setClassId} options={(classes.data??[]).map(c=>[c.id,c.name] as [number,string])}/><Select label="Subject" value={subjectId} onChange={setSubjectId} options={(subjects.data??[]).map(s=>[s.id,s.name] as [number,string])}/></div><button onClick={()=>assignMutation.mutate()} disabled={assignMutation.isPending || !teacherId || !classId || !subjectId} className="mt-5 rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white disabled:opacity-50">{assignMutation.isPending?"Assigning...":"Assign Teacher"}</button></section>
    {message && <p className="text-sm text-green-700">{message}</p>}{error && <p className="text-sm text-red-700">{error}</p>}
    <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-semibold">Existing teachers</h2><div className="mt-4 overflow-x-auto"><table className="min-w-full"><thead><tr className="border-b text-left text-xs uppercase text-slate-500"><th className="px-3 py-3">Teacher</th><th className="px-3 py-3">Email</th><th className="px-3 py-3">Status</th></tr></thead><tbody>{(teachers.data??[]).map(t=><tr key={t.id} className="border-b border-slate-100 text-sm"><td className="px-3 py-3 font-medium">{t.first_name} {t.last_name}</td><td className="px-3 py-3">{t.email??"No portal email"}</td><td className="px-3 py-3">{t.status}</td></tr>)}</tbody></table></div></section>
  </div></main>;
}
function Input({label,value,setValue,type="text",placeholder}:{label:string;value:string;setValue:(v:string)=>void;type?:string;placeholder?:string}){return <label className="block"><span className="text-sm font-medium text-slate-700">{label}</span><input type={type} value={value} onChange={e=>setValue(e.target.value)} placeholder={placeholder} className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"/></label>}
function Select({label,value,onChange,options}:{label:string;value:string;onChange:(v:string)=>void;options:[number,string][]}){return <label className="block"><span className="text-sm font-medium text-slate-700">{label}</span><select value={value} onChange={e=>onChange(e.target.value)} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"><option value="">Select {label.toLowerCase()}</option>{options.map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label>}
