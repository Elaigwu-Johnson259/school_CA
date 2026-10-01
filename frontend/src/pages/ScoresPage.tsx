import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import {
  calculateResult,
  createScore,
  fetchAssessmentTypes,
  fetchClasses,
  fetchSessions,
  fetchSubjects,
  fetchTerms,
} from "@/api/academic";
import { fetchStudents } from "@/api/students";

export function ScoresPage() {
  const [sessionId, setSessionId] = useState("");
  const [termId, setTermId] = useState("");
  const [classId, setClassId] = useState("");
  const [studentId, setStudentId] = useState("");
  const [subjectId, setSubjectId] = useState("");
  const [scores, setScores] = useState<Record<number, string>>({});
  const [result, setResult] = useState<{
    ca_total: number;
    exam_score: number;
    total: number;
  } | null>(null);
  const [error, setError] = useState("");

  const sessionsQuery = useQuery({
    queryKey: ["sessions"],
    queryFn: fetchSessions,
  });

  const termsQuery = useQuery({
    queryKey: ["scores-terms", sessionId],
    queryFn: () => fetchTerms(Number(sessionId)),
    enabled: Boolean(sessionId),
  });

  const classesQuery = useQuery({
    queryKey: ["classes"],
    queryFn: fetchClasses,
  });

  const studentsQuery = useQuery({
    queryKey: ["students"],
    queryFn: fetchStudents,
  });

  const subjectsQuery = useQuery({
    queryKey: ["subjects"],
    queryFn: fetchSubjects,
  });

  const assessmentTypesQuery = useQuery({
    queryKey: ["assessment-types"],
    queryFn: fetchAssessmentTypes,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!sessionId || !termId || !classId || !studentId || !subjectId) {
        throw new Error(
          "Please select session, term, class, student, and subject.",
        );
      }

      for (const assessment of assessmentTypesQuery.data ?? []) {
        const value = Number(scores[assessment.id] ?? 0);

        if (value > assessment.max_score) {
          throw new Error(
            `${assessment.name} cannot be greater than ${assessment.max_score}.`,
          );
        }

        await createScore({
          student_id: Number(studentId),
          subject_id: Number(subjectId),
          school_class_id: Number(classId),
          term_id: Number(termId),
          assessment_type_id: assessment.id,
          value,
        });
      }

      return calculateResult(
        Number(studentId),
        Number(subjectId),
        Number(termId),
      );
    },
    onSuccess: (data) => {
      setResult(data);
      setError("");
    },
    onError: (err: Error) => {
      setResult(null);
      setError(err.message);
    },
  });

  return (
    <div>
      <h1>Scores</h1>
      <p>Enter student assessment scores.</p>

      <div>
        <label>
          Academic Session
          <select
            value={sessionId}
            onChange={(event) => {
              setSessionId(event.target.value);
              setTermId("");
            }}
          >
            <option value="">Select session</option>
            {sessionsQuery.data?.map((session) => (
              <option key={session.id} value={session.id}>
                {session.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div>
        <label>
          Term
          <select
            value={termId}
            onChange={(event) => setTermId(event.target.value)}
            disabled={!sessionId}
          >
            <option value="">Select term</option>
            {termsQuery.data?.map((term) => (
              <option key={term.id} value={term.id}>
                {term.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div>
        <label>
          Class
          <select
            value={classId}
            onChange={(event) => setClassId(event.target.value)}
          >
            <option value="">Select class</option>
            {classesQuery.data?.map((schoolClass) => (
              <option key={schoolClass.id} value={schoolClass.id}>
                {schoolClass.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div>
        <label>
          Student
          <select
            value={studentId}
            onChange={(event) => setStudentId(event.target.value)}
          >
            <option value="">Select student</option>
            {studentsQuery.data?.map((student) => (
              <option key={student.id} value={student.id}>
                {student.admission_number} - {student.first_name}{" "}
                {student.last_name}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div>
        <label>
          Subject
          <select
            value={subjectId}
            onChange={(event) => setSubjectId(event.target.value)}
          >
            <option value="">Select subject</option>
            {subjectsQuery.data?.map((subject) => (
              <option key={subject.id} value={subject.id}>
                {subject.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {assessmentTypesQuery.data?.map((assessment) => (
        <div key={assessment.id}>
          <label>
            {assessment.name} ({assessment.max_score})
            <input
              type="number"
              min="0"
              max={assessment.max_score}
              value={scores[assessment.id] ?? ""}
              onChange={(event) =>
                setScores((current) => ({
                  ...current,
                  [assessment.id]: event.target.value,
                }))
              }
            />
          </label>
        </div>
      ))}

      <button
        type="button"
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
      >
        {saveMutation.isPending ? "Saving..." : "Save Scores"}
      </button>

      {error && <p>{error}</p>}

      {result && (
        <div>
          <h2>Result</h2>
          <p>CA Total: {result.ca_total} / 30</p>
          <p>Exam: {result.exam_score} / 70</p>
          <p>Total: {result.total} / 100</p>
        </div>
      )}
    </div>
  );
}
