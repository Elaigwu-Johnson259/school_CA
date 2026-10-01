import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createStudent,
  createStudentEnrollment,
  fetchStudents,
  type StudentPayload,
} from "@/api/students";
import {
  fetchClasses,
  fetchSessions,
  fetchTeacherAssignments,
} from "@/api/academic";
import type { Gender } from "@/types/enums";

const genderOptions: Gender[] = ["MALE", "FEMALE"];

export function StudentsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();

  const [admissionNumber, setAdmissionNumber] = useState("");
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [gender, setGender] = useState<Gender | "">("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [address, setAddress] = useState("");
  const [password, setPassword] = useState("");
  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");

  const isTeacher = user?.role === "TEACHER";

  const studentsQuery = useQuery({
    queryKey: ["students"],
    queryFn: fetchStudents,
  });

  const sessionsQuery = useQuery({
    queryKey: ["academic-sessions"],
    queryFn: fetchSessions,
    enabled: isTeacher,
  });

  const classesQuery = useQuery({
    queryKey: ["academic-classes"],
    queryFn: fetchClasses,
    enabled: isTeacher,
  });

  const assignmentsQuery = useQuery({
    queryKey: ["teacher-assignments"],
    queryFn: fetchTeacherAssignments,
    enabled: isTeacher,
  });


  const assignedClassIds = new Set(
    (assignmentsQuery.data ?? []).map((assignment) => assignment.school_class_id),
  );

  const assignedClasses = (classesQuery.data ?? []).filter((schoolClass) =>
    assignedClassIds.has(schoolClass.id),
  );

  const createMutation = useMutation({
    mutationFn: async (payload: StudentPayload) => {
      const student = await createStudent(payload);

      if (isTeacher) {
        await createStudentEnrollment({
          student_id: student.id,
          school_class_id: Number(selectedClassId),
          academic_session_id: Number(selectedSessionId),
        });
      }

      return student;
    },
    onSuccess: () => {
      setAdmissionNumber("");
      setFirstName("");
      setMiddleName("");
      setLastName("");
      setGender("");
      setDateOfBirth("");
      setGuardianName("");
      setGuardianPhone("");
      setAddress("");
      setPassword("");
      setSelectedSessionId("");
      setSelectedClassId("");

      queryClient.invalidateQueries({ queryKey: ["students"] });
      queryClient.invalidateQueries({ queryKey: ["student-enrollments"] });
    },
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (isTeacher && (!selectedSessionId || !selectedClassId)) {
      return;
    }

    createMutation.mutate({
      admission_number: admissionNumber.trim(),
      first_name: firstName.trim(),
      middle_name: middleName.trim() || null,
      last_name: lastName.trim(),
      gender: gender || null,
      date_of_birth: dateOfBirth || null,
      guardian_name: guardianName.trim() || null,
      guardian_phone: guardianPhone.trim() || null,
      address: address.trim() || null,
      password: password.trim() || undefined,
    });
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <header>
          <Link
            to="/dashboard"
            className="mb-4 inline-flex items-center text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            ← Back to Dashboard
          </Link>
          <p className="text-sm font-medium text-slate-500">
            People Management
          </p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Students</h1>
          <p className="mt-2 text-slate-600">
            {isTeacher
              ? "Create students and enroll them in classes you are assigned to."
              : "Add and manage the students enrolled in your school."}
          </p>
        </header>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">
            Add student
          </h2>

          <form
            onSubmit={handleSubmit}
            className="mt-6 grid gap-5 md:grid-cols-2"
          >
            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Admission number
              </span>
              <input
                required
                value={admissionNumber}
                onChange={(event) => setAdmissionNumber(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="JSA002"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                First name
              </span>
              <input
                required
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="John"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Middle name
              </span>
              <input
                value={middleName}
                onChange={(event) => setMiddleName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Peter"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Last name
              </span>
              <input
                required
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Johnson"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Gender
              </span>
              <select
                value={gender}
                onChange={(event) =>
                  setGender(event.target.value as Gender | "")
                }
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">Select gender</option>
                {genderOptions.map((option) => (
                  <option key={option} value={option}>
                    {option === "MALE" ? "Male" : "Female"}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Date of birth
              </span>
              <input
                type="date"
                value={dateOfBirth}
                onChange={(event) => setDateOfBirth(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
              />
            </label>

            {isTeacher && (
              <>
                <label className="block">
                  <span className="text-sm font-medium text-slate-700">
                    Academic session
                  </span>
                  <select
                    required
                    value={selectedSessionId}
                    onChange={(event) =>
                      setSelectedSessionId(event.target.value)
                    }
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                  >
                    <option value="">Select session</option>
                    {sessionsQuery.data?.map((session) => (
                      <option key={session.id} value={session.id}>
                        {session.name}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="block">
                  <span className="text-sm font-medium text-slate-700">
                    Assigned class
                  </span>
                  <select
                    required
                    value={selectedClassId}
                    onChange={(event) => setSelectedClassId(event.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                  >
                    <option value="">Select assigned class</option>
                    {assignedClasses.map((schoolClass) => (
                      <option key={schoolClass.id} value={schoolClass.id}>
                        {schoolClass.name}
                      </option>
                    ))}
                  </select>
                </label>
              </>
            )}

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Guardian name
              </span>
              <input
                value={guardianName}
                onChange={(event) => setGuardianName(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Parent or guardian"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Guardian phone
              </span>
              <input
                value={guardianPhone}
                onChange={(event) => setGuardianPhone(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="08012345678"
              />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Student portal password
              </span>
              <input
                type="password"
                minLength={8}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Optional — enables student login"
              />
            </label>

            <label className="block md:col-span-2">
              <span className="text-sm font-medium text-slate-700">
                Address
              </span>
              <textarea
                value={address}
                onChange={(event) => setAddress(event.target.value)}
                rows={3}
                className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                placeholder="Student's home address"
              />
            </label>

            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={
                  createMutation.isPending ||
                  (isTeacher &&
                    (!selectedSessionId ||
                      !selectedClassId ||
                      assignmentsQuery.isLoading))
                }
                className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createMutation.isPending
                  ? isTeacher
                    ? "Creating and enrolling..."
                    : "Creating..."
                  : isTeacher
                    ? "Create and enroll student"
                    : "Add student"}
              </button>

              {createMutation.isSuccess && (
                <p className="mt-3 text-sm text-green-700">
                  {isTeacher
                    ? "Student created and enrolled successfully."
                    : "Student created successfully."}
                </p>
              )}

              {createMutation.isError && (
                <p className="mt-3 text-sm text-red-700">
                  Unable to create or enroll student. Please check the
                  information and try again.
                </p>
              )}
            </div>
          </form>

          {isTeacher && !assignmentsQuery.isLoading && assignedClasses.length === 0 && (
            <p className="mt-4 text-sm text-amber-700">
              You are not currently assigned to any classes.
            </p>
          )}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">
            {isTeacher ? "Your students" : "Existing students"}
          </h2>

          {studentsQuery.isLoading && (
            <p className="mt-4 text-sm text-slate-500">Loading students...</p>
          )}

          {studentsQuery.isError && (
            <p className="mt-4 text-sm text-red-700">
              Unable to load students.
            </p>
          )}

          {studentsQuery.isSuccess && studentsQuery.data.length === 0 && (
            <p className="mt-4 text-sm text-slate-500">
              No students have been created yet.
            </p>
          )}

          {studentsQuery.isSuccess && studentsQuery.data.length > 0 && (
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200">
                <thead>
                  <tr className="text-left text-sm text-slate-500">
                    <th className="px-3 py-3 font-medium">Admission No.</th>
                    <th className="px-3 py-3 font-medium">Student</th>
                    <th className="px-3 py-3 font-medium">Gender</th>
                    <th className="px-3 py-3 font-medium">Status</th>
                    <th className="px-3 py-3 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {studentsQuery.data.map((student) => (
                    <tr key={student.id} className="text-sm text-slate-700">
                      <td className="px-3 py-3 font-medium text-slate-900">
                        {student.admission_number}
                      </td>
                      <td className="px-3 py-3">
                        {[
                          student.first_name,
                          student.middle_name,
                          student.last_name,
                        ]
                          .filter(Boolean)
                          .join(" ")}
                      </td>
                      <td className="px-3 py-3">
                        {student.gender
                          ? student.gender === "MALE"
                            ? "Male"
                            : "Female"
                          : "—"}
                      </td>
                      <td className="px-3 py-3">{student.status}</td>
                      <td className="px-3 py-3">
                        <Link
                          to={`/students/${student.id}`}
                          className="font-medium text-slate-700 hover:text-slate-900 hover:underline"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
