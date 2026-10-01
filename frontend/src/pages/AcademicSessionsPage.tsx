import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createClass,
  createClassSubject,
  createSession,
  createSubject,
  fetchClassSubjects,
  fetchClasses,
  fetchSessions,
  fetchSubjects,
  updateSession,
} from "@/api/academic";

export function AcademicSessionsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [isCurrent, setIsCurrent] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");

  const [className, setClassName] = useState("");
  const [subjectName, setSubjectName] = useState("");
  const [subjectCode, setSubjectCode] = useState("");
  const [selectedClassId, setSelectedClassId] = useState("");
  const [selectedSubjectId, setSelectedSubjectId] = useState("");

  const {
    data: sessions = [],
    isLoading: sessionsLoading,
    isError: sessionsError,
  } = useQuery({
    queryKey: ["academic-sessions"],
    queryFn: fetchSessions,
  });

  const {
    data: classes = [],
    isLoading: classesLoading,
    isError: classesError,
  } = useQuery({
    queryKey: ["academic-classes"],
    queryFn: fetchClasses,
  });

  const {
    data: subjects = [],
    isLoading: subjectsLoading,
    isError: subjectsError,
  } = useQuery({
    queryKey: ["academic-subjects"],
    queryFn: fetchSubjects,
  });

  const {
    data: classSubjects = [],
    isLoading: classSubjectsLoading,
  } = useQuery({
    queryKey: ["academic-class-subjects", selectedClassId],
    queryFn: () => fetchClassSubjects(Number(selectedClassId)),
    enabled: Boolean(selectedClassId),
  });

  const createMutation = useMutation({
    mutationFn: () => createSession(name.trim(), isCurrent),
    onSuccess: () => {
      setName("");
      setIsCurrent(false);
      queryClient.invalidateQueries({ queryKey: ["academic-sessions"] });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: number;
      updates: { name?: string; is_current?: boolean };
    }) => updateSession(id, updates),
    onSuccess: () => {
      setEditingId(null);
      setEditingName("");
      queryClient.invalidateQueries({ queryKey: ["academic-sessions"] });
    },
  });

  const createClassMutation = useMutation({
    mutationFn: () => createClass(className.trim()),
    onSuccess: () => {
      setClassName("");
      queryClient.invalidateQueries({ queryKey: ["academic-classes"] });
    },
  });

  const createSubjectMutation = useMutation({
    mutationFn: () => createSubject(subjectName.trim(), subjectCode.trim()),
    onSuccess: () => {
      setSubjectName("");
      setSubjectCode("");
      queryClient.invalidateQueries({ queryKey: ["academic-subjects"] });
    },
  });

  const createClassSubjectMutation = useMutation({
    mutationFn: () =>
      createClassSubject(
        Number(selectedClassId),
        Number(selectedSubjectId),
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["academic-class-subjects", selectedClassId],
      });
      setSelectedSubjectId("");
    },
  });

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();

    if (!name.trim()) {
      return;
    }

    createMutation.mutate();
  }

  function startEditing(id: number, currentName: string) {
    setEditingId(id);
    setEditingName(currentName);
  }

  function saveEdit(id: number) {
    if (!editingName.trim()) {
      return;
    }

    updateMutation.mutate({
      id,
      updates: { name: editingName.trim() },
    });
  }

  function handleCreateClass(event: React.FormEvent) {
    event.preventDefault();

    if (!className.trim()) {
      return;
    }

    createClassMutation.mutate();
  }

  function handleCreateSubject(event: React.FormEvent) {
    event.preventDefault();

    if (!subjectName.trim() || !subjectCode.trim()) {
      return;
    }

    createSubjectMutation.mutate();
  }

  function handleCreateClassSubject(event: React.FormEvent) {
    event.preventDefault();

    if (!selectedClassId || !selectedSubjectId) {
      return;
    }

    createClassSubjectMutation.mutate();
  }

  const linkedSubjectIds = new Set(
    classSubjects.map((classSubject) => classSubject.subject_id),
  );

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link
            to="/dashboard"
            className="mb-4 inline-flex items-center text-sm font-medium text-slate-600 hover:text-slate-900"
          >
            ← Back to Dashboard
          </Link>
          <p className="text-sm font-medium text-slate-500">
            Academic Management
          </p>
          <h1 className="mt-1 text-2xl font-semibold text-slate-900">
            Academic Management
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Manage academic sessions, classes, subjects, and the subjects
            taught in each class.
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Create academic session
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Example: 2026/2027 Session
          </p>

          <form
            onSubmit={handleCreate}
            className="mt-5 flex flex-col gap-4 sm:flex-row sm:items-end"
          >
            <div className="flex-1">
              <label
                htmlFor="session-name"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Session name
              </label>
              <input
                id="session-name"
                type="text"
                value={name}
                onChange={(event) => setName(event.target.value)}
                placeholder="2026/2027 Session"
                maxLength={20}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <label className="flex items-center gap-2 pb-2.5 text-sm text-slate-700">
              <input
                type="checkbox"
                checked={isCurrent}
                onChange={(event) => setIsCurrent(event.target.checked)}
                className="h-4 w-4 rounded border-slate-300"
              />
              Set as current
            </label>

            <button
              type="submit"
              disabled={!name.trim() || createMutation.isPending}
              className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {createMutation.isPending ? "Creating…" : "Create session"}
            </button>
          </form>

          {createMutation.isError && (
            <p className="mt-3 text-sm text-red-600">
              Unable to create the session. Please try again.
            </p>
          )}

          {createMutation.isSuccess && (
            <p className="mt-3 text-sm text-emerald-600">
              Academic session created successfully.
            </p>
          )}
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-base font-semibold text-slate-900">
              Existing sessions
            </h2>
          </div>

          {sessionsLoading && (
            <p className="px-6 py-8 text-sm text-slate-500">
              Loading academic sessions…
            </p>
          )}

          {sessionsError && (
            <p className="px-6 py-8 text-sm text-red-600">
              Unable to load academic sessions.
            </p>
          )}

          {!sessionsLoading && !sessionsError && sessions.length === 0 && (
            <p className="px-6 py-8 text-sm text-slate-500">
              No academic sessions have been created yet.
            </p>
          )}

          {!sessionsLoading && !sessionsError && sessions.length > 0 && (
            <div className="divide-y divide-slate-100">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div>
                    {editingId === session.id ? (
                      <input
                        value={editingName}
                        onChange={(event) => setEditingName(event.target.value)}
                        maxLength={20}
                        className="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
                      />
                    ) : (
                      <div className="flex items-center gap-3">
                        <span className="font-medium text-slate-900">
                          {session.name}
                        </span>

                        {session.is_current && (
                          <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                            Current
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    {editingId === session.id ? (
                      <>
                        <button
                          type="button"
                          onClick={() => saveEdit(session.id)}
                          disabled={
                            !editingName.trim() || updateMutation.isPending
                          }
                          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingId(null);
                            setEditingName("");
                          }}
                          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        {!session.is_current && (
                          <button
                            type="button"
                            onClick={() =>
                              updateMutation.mutate({
                                id: session.id,
                                updates: { is_current: true },
                              })
                            }
                            disabled={updateMutation.isPending}
                            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                          >
                            Make current
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() =>
                            navigate(`/academic/sessions/${session.id}/terms`)
                          }
                          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Manage terms
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            startEditing(session.id, session.name)
                          }
                          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Edit
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Classes
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Create the classes used by your school.
          </p>

          <form
            onSubmit={handleCreateClass}
            className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-end"
          >
            <div className="flex-1">
              <label
                htmlFor="class-name"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Class name
              </label>
              <input
                id="class-name"
                type="text"
                value={className}
                onChange={(event) => setClassName(event.target.value)}
                placeholder="JSS 1A"
                maxLength={100}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <button
              type="submit"
              disabled={!className.trim() || createClassMutation.isPending}
              className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {createClassMutation.isPending ? "Creating…" : "Create class"}
            </button>
          </form>

          {createClassMutation.isError && (
            <p className="mt-3 text-sm text-red-600">
              Unable to create the class. Please try again.
            </p>
          )}

          {createClassMutation.isSuccess && (
            <p className="mt-3 text-sm text-emerald-600">
              Class created successfully.
            </p>
          )}

          <div className="mt-6">
            <h3 className="text-sm font-semibold text-slate-800">
              Existing classes
            </h3>

            {classesLoading && (
              <p className="mt-3 text-sm text-slate-500">Loading classes…</p>
            )}

            {classesError && (
              <p className="mt-3 text-sm text-red-600">
                Unable to load classes.
              </p>
            )}

            {!classesLoading && !classesError && classes.length === 0 && (
              <p className="mt-3 text-sm text-slate-500">
                No classes have been created yet.
              </p>
            )}

            {!classesLoading && !classesError && classes.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {classes.map((schoolClass) => (
                  <span
                    key={schoolClass.id}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700"
                  >
                    {schoolClass.name}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Subjects
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Create subjects with a name and subject code.
          </p>

          <form
            onSubmit={handleCreateSubject}
            className="mt-5 grid gap-4 sm:grid-cols-2"
          >
            <div>
              <label
                htmlFor="subject-name"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Subject name
              </label>
              <input
                id="subject-name"
                type="text"
                value={subjectName}
                onChange={(event) => setSubjectName(event.target.value)}
                placeholder="Mathematics"
                maxLength={100}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label
                htmlFor="subject-code"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Subject code
              </label>
              <input
                id="subject-code"
                type="text"
                value={subjectCode}
                onChange={(event) => setSubjectCode(event.target.value)}
                placeholder="MATH"
                maxLength={20}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm uppercase outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={
                  !subjectName.trim() ||
                  !subjectCode.trim() ||
                  createSubjectMutation.isPending
                }
                className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {createSubjectMutation.isPending
                  ? "Creating…"
                  : "Create subject"}
              </button>
            </div>
          </form>

          {createSubjectMutation.isError && (
            <p className="mt-3 text-sm text-red-600">
              Unable to create the subject. Please try again.
            </p>
          )}

          {createSubjectMutation.isSuccess && (
            <p className="mt-3 text-sm text-emerald-600">
              Subject created successfully.
            </p>
          )}

          <div className="mt-6">
            <h3 className="text-sm font-semibold text-slate-800">
              Existing subjects
            </h3>

            {subjectsLoading && (
              <p className="mt-3 text-sm text-slate-500">Loading subjects…</p>
            )}

            {subjectsError && (
              <p className="mt-3 text-sm text-red-600">
                Unable to load subjects.
              </p>
            )}

            {!subjectsLoading && !subjectsError && subjects.length === 0 && (
              <p className="mt-3 text-sm text-slate-500">
                No subjects have been created yet.
              </p>
            )}

            {!subjectsLoading && !subjectsError && subjects.length > 0 && (
              <div className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-200">
                {subjects.map((subject) => (
                  <div
                    key={subject.id}
                    className="flex items-center justify-between px-4 py-3"
                  >
                    <span className="font-medium text-slate-800">
                      {subject.name}
                    </span>
                    <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                      {subject.code}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Class subjects
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Link subjects to the classes where they are taught.
          </p>

          <form
            onSubmit={handleCreateClassSubject}
            className="mt-5 grid gap-4 sm:grid-cols-3 sm:items-end"
          >
            <div>
              <label
                htmlFor="link-class"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Class
              </label>
              <select
                id="link-class"
                value={selectedClassId}
                onChange={(event) => {
                  setSelectedClassId(event.target.value);
                  setSelectedSubjectId("");
                }}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              >
                <option value="">Select class</option>
                {classes.map((schoolClass) => (
                  <option key={schoolClass.id} value={schoolClass.id}>
                    {schoolClass.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="link-subject"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Subject
              </label>
              <select
                id="link-subject"
                value={selectedSubjectId}
                onChange={(event) => setSelectedSubjectId(event.target.value)}
                disabled={!selectedClassId}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200 disabled:bg-slate-50"
              >
                <option value="">Select subject</option>
                {subjects
                  .filter((subject) => !linkedSubjectIds.has(subject.id))
                  .map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.name} ({subject.code})
                    </option>
                  ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={
                !selectedClassId ||
                !selectedSubjectId ||
                createClassSubjectMutation.isPending
              }
              className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {createClassSubjectMutation.isPending
                ? "Linking…"
                : "Add subject to class"}
            </button>
          </form>

          {createClassSubjectMutation.isError && (
            <p className="mt-3 text-sm text-red-600">
              Unable to link:{" "}
              {createClassSubjectMutation.error instanceof Error
                ? createClassSubjectMutation.error.message
                : "Unknown error"}
            </p>
          )}

          {createClassSubjectMutation.isSuccess && (
            <p className="mt-3 text-sm text-emerald-600">
              Subject linked to class successfully.
            </p>
          )}

          {selectedClassId && (
            <div className="mt-6">
              <h3 className="text-sm font-semibold text-slate-800">
                Subjects in selected class
              </h3>

              {classSubjectsLoading && (
                <p className="mt-3 text-sm text-slate-500">
                  Loading class subjects…
                </p>
              )}

              {!classSubjectsLoading && classSubjects.length === 0 && (
                <p className="mt-3 text-sm text-slate-500">
                  No subjects have been linked to this class yet.
                </p>
              )}

              {!classSubjectsLoading && classSubjects.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {classSubjects.map((classSubject) => {
                    const subject = subjects.find(
                      (item) => item.id === classSubject.subject_id,
                    );

                    return (
                      <span
                        key={classSubject.id}
                        className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700"
                      >
                        {subject
                          ? `${subject.name} (${subject.code})`
                          : `Subject #${classSubject.subject_id}`}
                      </span>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
