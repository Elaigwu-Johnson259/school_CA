import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createStudent,
  fetchStudents,
  type StudentPayload,
} from "@/api/students";
import type { Gender } from "@/types/enums";

const genderOptions: Gender[] = ["MALE", "FEMALE"];

export function StudentsPage() {
  const queryClient = useQueryClient();

  const [admissionNumber, setAdmissionNumber] = useState("");
  const [firstName, setFirstName] = useState("");
  const [middleName, setMiddleName] = useState("");
  const [lastName, setLastName] = useState("");
  const [gender, setGender] = useState<Gender | "">("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [guardianName, setGuardianName] = useState("");
  const [guardianPhone, setGuardianPhone] = useState("");
  const [address, setAddress] = useState("");

  const studentsQuery = useQuery({
    queryKey: ["students"],
    queryFn: fetchStudents,
  });

  const createMutation = useMutation({
    mutationFn: (payload: StudentPayload) => createStudent(payload),
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

      queryClient.invalidateQueries({ queryKey: ["students"] });
    },
  });

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

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
    });
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-6xl space-y-8">
        <header>
          <p className="text-sm font-medium text-slate-500">People Management</p>
          <h1 className="mt-1 text-3xl font-bold text-slate-900">Students</h1>
          <p className="mt-2 text-slate-600">
            Add and manage the students enrolled in your school.
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
                disabled={createMutation.isPending}
                className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {createMutation.isPending ? "Creating..." : "Add student"}
              </button>

              {createMutation.isSuccess && (
                <p className="mt-3 text-sm text-green-700">
                  Student created successfully.
                </p>
              )}

              {createMutation.isError && (
                <p className="mt-3 text-sm text-red-700">
                  Unable to create student. Please check the information and
                  try again.
                </p>
              )}
            </div>
          </form>
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-900">
            Existing students
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
