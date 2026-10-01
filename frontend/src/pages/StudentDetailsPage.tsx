import { Link, useParams } from "react-router-dom";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createStudentEnrollment,
  deleteStudentEnrollment,
  fetchStudent,
  fetchStudentEnrollments,
  updateStudent,
} from "@/api/students";
import { fetchClasses, fetchSessions } from "@/api/academic";

export function StudentDetailsPage() {
  const { studentId } = useParams();
  const queryClient = useQueryClient();

  const [isEditing, setIsEditing] = useState(false);
  const [admissionNumber, setAdmissionNumber] = useState("");
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [gender, setGender] = useState<"MALE" | "FEMALE" | "">("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [address, setAddress] = useState("");

  const studentQuery = useQuery({
    queryKey: ["student", studentId],
    queryFn: () => fetchStudent(Number(studentId)),
    enabled: Boolean(studentId),
  });

  const enrollmentsQuery = useQuery({
    queryKey: ["student-enrollments"],
    queryFn: fetchStudentEnrollments,
  });

  const sessionsQuery = useQuery({
    queryKey: ["academic-sessions"],
    queryFn: fetchSessions,
  });

  const classesQuery = useQuery({
    queryKey: ["academic-classes"],
    queryFn: fetchClasses,
  });

  const [selectedSessionId, setSelectedSessionId] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");

  const enrollmentMutation = useMutation({
    mutationFn: () =>
      createStudentEnrollment({
        student_id: Number(studentId),
        school_class_id: Number(selectedClassId),
        academic_session_id: Number(selectedSessionId),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["student-enrollments"],
      });
      setSelectedSessionId("");
      setSelectedClassId("");
    },
  });

  const deleteEnrollmentMutation = useMutation({
    mutationFn: (enrollmentId: number) =>
      deleteStudentEnrollment(enrollmentId),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["student-enrollments"],
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: () =>
      updateStudent(Number(studentId), {
        admission_number: admissionNumber.trim(),
        first_name: firstName.trim(),
        middle_name: middleName.trim() || null,
        last_name: lastName.trim(),
        gender: gender || null,
        date_of_birth: dateOfBirth || null,
        guardian_name: guardianName.trim() || null,
        guardian_phone: guardianPhone.trim() || null,
        address: address.trim() || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["student", studentId],
      });
      queryClient.invalidateQueries({
        queryKey: ["students"],
      });
      setIsEditing(false);
    },
  });

  if (studentQuery.isLoading) {
    return (
      <main className="min-h-screen bg-slate-50 px-4 py-8">
        <div className="mx-auto max-w-4xl">
          <p className="text-sm text-slate-500">Loading student...</p>
        </div>
      </main>
    );
  }

  if (studentQuery.isError || !studentQuery.data) {
    return (
      <main className="min-h-screen bg-slate-50 px-4 py-8">
        <div className="mx-auto max-w-4xl">
          <p className="text-sm text-red-700">Unable to load student.</p>
          <Link
            to="/students"
            className="mt-4 inline-block text-sm font-medium text-slate-700 underline"
          >
            Back to students
          </Link>
        </div>
      </main>
    );
  }

  const student = studentQuery.data;

  function startEditing() {
    setAdmissionNumber(student.admission_number);
    setFirstName(student.first_name);
    setMiddleName(student.middle_name ?? "");
    setLastName(student.last_name);
    setGender(student.gender ?? "");
    setDateOfBirth(student.date_of_birth ?? "");
    setGuardianName(student.guardian_name ?? "");
    setGuardianPhone(student.guardian_phone ?? "");
    setAddress(student.address ?? "");
    setIsEditing(true);
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <div>
          <Link
            to="/students"
            className="text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            ← Back to students
          </Link>

          <p className="mt-4 text-sm font-medium text-slate-500">
            Student details
          </p>

          <div className="mt-1 flex items-center justify-between gap-4">
            <h1 className="text-3xl font-bold text-slate-900">
              {[
                student.first_name,
                student.middle_name,
                student.last_name,
              ]
                .filter(Boolean)
                .join(" ")}
            </h1>

            {!isEditing && (
              <button
                type="button"
                onClick={startEditing}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              >
                Edit student
              </button>
            )}
          </div>
        </div>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">
            {isEditing ? "Edit student" : "Student information"}
          </h2>

          {!isEditing ? (
            <dl className="mt-6 grid gap-5 md:grid-cols-2">
              <div>
                <dt className="text-sm text-slate-500">Admission number</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.admission_number}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Gender</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.gender === "MALE"
                    ? "Male"
                    : student.gender === "FEMALE"
                      ? "Female"
                      : "—"}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Date of birth</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.date_of_birth || "—"}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Status</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.status}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Guardian name</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.guardian_name || "—"}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Guardian phone</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.guardian_phone || "—"}
                </dd>
              </div>

              <div className="md:col-span-2">
                <dt className="text-sm text-slate-500">Address</dt>
                <dd className="mt-1 font-medium text-slate-900">
                  {student.address || "—"}
                </dd>
              </div>
            </dl>
          ) : (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                updateMutation.mutate();
              }}
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
                />
              </label>

              <label className="block">
                <span className="text-sm font-medium text-slate-700">
                  Gender
                </span>
                <select
                  value={gender}
                  onChange={(event) =>
                    setGender(event.target.value as "MALE" | "FEMALE" | "")
                  }
                  className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
                >
                  <option value="">Select gender</option>
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
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

              <label className="block">
                <span className="text-sm font-medium text-slate-700">
                  Guardian name
                </span>
                <input
                  value={guardianName}
                  onChange={(event) => setGuardianName(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
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
                />
              </label>

              <label className="block md:col-span-2">
                <span className="text-sm font-medium text-slate-700">
                  Address
                </span>
                <textarea
                  rows={3}
                  value={address}
                  onChange={(event) => setAddress(event.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2"
                />
              </label>

              <div className="flex gap-3 md:col-span-2">
                <button
                  type="submit"
                  disabled={updateMutation.isPending}
                  className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {updateMutation.isPending ? "Saving..." : "Save changes"}
                </button>

                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  disabled={updateMutation.isPending}
                  className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                >
                  Cancel
                </button>
              </div>

              {updateMutation.isError && (
                <p className="text-sm text-red-700 md:col-span-2">
                  Unable to update student. Please check the information and
                  try again.
                </p>
              )}

              {updateMutation.isSuccess && (
                <p className="text-sm text-green-700 md:col-span-2">
                  Student updated successfully.
                </p>
              )}
            </form>
          )}
        </section>
        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <div>
            <h2 className="text-xl font-semibold text-slate-900">
              Academic enrollment
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Enroll this student in a class for an academic session.
            </p>
          </div>

          <form
            onSubmit={(event) => {
              event.preventDefault();
              enrollmentMutation.mutate();
            }}
            className="mt-6 grid gap-4 md:grid-cols-3"
          >
            <label className="block">
              <span className="text-sm font-medium text-slate-700">
                Academic session
              </span>
              <select
                required
                value={selectedSessionId}
                onChange={(event) => setSelectedSessionId(event.target.value)}
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
                Class
              </span>
              <select
                required
                value={selectedClassId}
                onChange={(event) => setSelectedClassId(event.target.value)}
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2"
              >
                <option value="">Select class</option>
                {classesQuery.data?.map((schoolClass) => (
                  <option key={schoolClass.id} value={schoolClass.id}>
                    {schoolClass.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="flex items-end">
              <button
                type="submit"
                disabled={
                  enrollmentMutation.isPending ||
                  !selectedSessionId ||
                  !selectedClassId
                }
                className="w-full rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {enrollmentMutation.isPending
                  ? "Enrolling..."
                  : "Enroll student"}
              </button>
            </div>
          </form>

          {enrollmentMutation.isError && (
            <p className="mt-4 text-sm text-red-700">
              Unable to create enrollment. Please check the selected session
              and class.
            </p>
          )}

          <div className="mt-8">
            <h3 className="text-sm font-semibold text-slate-900">
              Current enrollments
            </h3>

            {enrollmentsQuery.isLoading ? (
              <p className="mt-3 text-sm text-slate-500">
                Loading enrollments...
              </p>
            ) : enrollmentsQuery.data?.filter(
                (enrollment) => enrollment.student_id === Number(studentId),
              ).length === 0 ? (
              <p className="mt-3 text-sm text-slate-500">
                This student has no enrollments yet.
              </p>
            ) : (
              <div className="mt-3 space-y-2">
                {enrollmentsQuery.data
                  ?.filter(
                    (enrollment) =>
                      enrollment.student_id === Number(studentId),
                  )
                  .map((enrollment) => {
                    const session = sessionsQuery.data?.find(
                      (item) => item.id === enrollment.academic_session_id,
                    );
                    const schoolClass = classesQuery.data?.find(
                      (item) => item.id === enrollment.school_class_id,
                    );

                    return (
                      <div
                        key={enrollment.id}
                        className="flex items-center justify-between rounded-lg border border-slate-200 px-4 py-3"
                      >
                        <div>
                          <p className="font-medium text-slate-900">
                            {schoolClass?.name ?? "Unknown class"}
                          </p>
                          <p className="text-sm text-slate-500">
                            {session?.name ?? "Unknown session"}
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() =>
                            deleteEnrollmentMutation.mutate(enrollment.id)
                          }
                          disabled={deleteEnrollmentMutation.isPending}
                          className="text-sm font-medium text-red-600 hover:text-red-700 disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </div>
                    );
                  })}
              </div>
            )}
          </div>
        </section>

      </div>
    </main>
  );
}
