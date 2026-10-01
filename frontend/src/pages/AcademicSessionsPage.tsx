import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createSession,
  fetchSessions,
  updateSession,
} from "@/api/academic";

export function AcademicSessionsPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [name, setName] = useState("");
  const [isCurrent, setIsCurrent] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState("");

  const {
    data: sessions = [],
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["academic-sessions"],
    queryFn: fetchSessions,
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
            Academic Sessions
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Create and manage the academic sessions used by your school.
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

          {isLoading && (
            <p className="px-6 py-8 text-sm text-slate-500">
              Loading academic sessions…
            </p>
          )}

          {isError && (
            <p className="px-6 py-8 text-sm text-red-600">
              Unable to load academic sessions.
            </p>
          )}

          {!isLoading && !isError && sessions.length === 0 && (
            <p className="px-6 py-8 text-sm text-slate-500">
              No academic sessions have been created yet.
            </p>
          )}

          {!isLoading && !isError && sessions.length > 0 && (
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
      </div>
    </div>
  );
}
