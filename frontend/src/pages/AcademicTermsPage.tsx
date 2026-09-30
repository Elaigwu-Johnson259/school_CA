import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTerm,
  fetchSessions,
  fetchTerms,
  updateTerm,
} from "@/api/academic";
import type { TermName } from "@/types/enums";

const termOptions: TermName[] = ["FIRST", "SECOND", "THIRD"];

const termLabels: Record<TermName, string> = {
  FIRST: "First Term",
  SECOND: "Second Term",
  THIRD: "Third Term",
};

export function AcademicTermsPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const queryClient = useQueryClient();

  const parsedSessionId = Number(sessionId);

  const [termName, setTermName] = useState<TermName>("FIRST");
  const [isCurrent, setIsCurrent] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingName, setEditingName] = useState<TermName>("FIRST");
  const [editingStartDate, setEditingStartDate] = useState("");
  const [editingEndDate, setEditingEndDate] = useState("");

  const sessionsQuery = useQuery({
    queryKey: ["academic-sessions"],
    queryFn: fetchSessions,
  });

  const termsQuery = useQuery({
    queryKey: ["academic-terms", parsedSessionId],
    queryFn: () => fetchTerms(parsedSessionId),
    enabled: Number.isInteger(parsedSessionId) && parsedSessionId > 0,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createTerm(parsedSessionId, {
        name: termName,
        is_current: isCurrent,
        start_date: startDate || null,
        end_date: endDate || null,
      }),
    onSuccess: () => {
      setTermName("FIRST");
      setIsCurrent(false);
      setStartDate("");
      setEndDate("");
      queryClient.invalidateQueries({
        queryKey: ["academic-terms", parsedSessionId],
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      updates,
    }: {
      id: number;
      updates: {
        name?: TermName;
        start_date?: string | null;
        end_date?: string | null;
      };
    }) => updateTerm(id, updates),
    onSuccess: () => {
      setEditingId(null);
      queryClient.invalidateQueries({
        queryKey: ["academic-terms", parsedSessionId],
      });
    },
  });

  const session = sessionsQuery.data?.find(
    (item) => item.id === parsedSessionId,
  );

  function handleCreate(event: React.FormEvent) {
    event.preventDefault();

    if (!session || createMutation.isPending) {
      return;
    }

    createMutation.mutate();
  }

  function startEditing(
    id: number,
    name: TermName,
    startDateValue: string | null,
    endDateValue: string | null,
  ) {
    setEditingId(id);
    setEditingName(name);
    setEditingStartDate(startDateValue ?? "");
    setEditingEndDate(endDateValue ?? "");
  }

  function saveEdit(id: number) {
    updateMutation.mutate({
      id,
      updates: {
        name: editingName,
        start_date: editingStartDate || null,
        end_date: editingEndDate || null,
      },
    });
  }

  if (!sessionId || !Number.isInteger(parsedSessionId) || parsedSessionId <= 0) {
    return (
      <div className="min-h-screen bg-slate-50 px-4 py-8">
        <div className="mx-auto max-w-5xl rounded-xl border border-red-200 bg-white p-6">
          <h1 className="text-lg font-semibold text-red-700">
            Invalid academic session
          </h1>
          <Link
            to="/academic/sessions"
            className="mt-4 inline-block text-sm font-medium text-slate-700 underline"
          >
            Back to academic sessions
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link
            to="/academic/sessions"
            className="text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            ← Academic Sessions
          </Link>

          <p className="mt-5 text-sm font-medium text-slate-500">
            Academic Management
          </p>

          <h1 className="mt-1 text-2xl font-semibold text-slate-900">
            Academic Terms
          </h1>

          <p className="mt-1 text-sm text-slate-600">
            {session
              ? `Manage terms for ${session.name}.`
              : "Manage the terms for this academic session."}
          </p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-base font-semibold text-slate-900">
            Create academic term
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Add a term and optionally set it as the current term.
          </p>

          <form
            onSubmit={handleCreate}
            className="mt-5 grid gap-4 sm:grid-cols-2"
          >
            <div>
              <label
                htmlFor="term-name"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Term
              </label>
              <select
                id="term-name"
                value={termName}
                onChange={(event) =>
                  setTermName(event.target.value as TermName)
                }
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              >
                {termOptions.map((option) => (
                  <option key={option} value={option}>
                    {termLabels[option]}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-end">
              <label className="flex items-center gap-2 pb-2.5 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={isCurrent}
                  onChange={(event) => setIsCurrent(event.target.checked)}
                  className="h-4 w-4 rounded border-slate-300"
                />
                Set as current
              </label>
            </div>

            <div>
              <label
                htmlFor="term-start-date"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                Start date
              </label>
              <input
                id="term-start-date"
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div>
              <label
                htmlFor="term-end-date"
                className="mb-1.5 block text-sm font-medium text-slate-700"
              >
                End date
              </label>
              <input
                id="term-end-date"
                type="date"
                value={endDate}
                onChange={(event) => setEndDate(event.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-slate-500 focus:ring-2 focus:ring-slate-200"
              />
            </div>

            <div className="sm:col-span-2">
              <button
                type="submit"
                disabled={!session || createMutation.isPending}
                className="rounded-lg bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {createMutation.isPending ? "Creating…" : "Create term"}
              </button>
            </div>
          </form>

          {createMutation.isError && (
            <p className="mt-3 text-sm text-red-600">
              Unable to create the term. Please try again.
            </p>
          )}

          {createMutation.isSuccess && (
            <p className="mt-3 text-sm text-emerald-600">
              Academic term created successfully.
            </p>
          )}
        </div>

        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-base font-semibold text-slate-900">
              Existing terms
            </h2>
          </div>

          {sessionsQuery.isLoading || termsQuery.isLoading ? (
            <p className="px-6 py-8 text-sm text-slate-500">
              Loading academic terms…
            </p>
          ) : sessionsQuery.isError || termsQuery.isError ? (
            <p className="px-6 py-8 text-sm text-red-600">
              Unable to load academic terms.
            </p>
          ) : termsQuery.data?.length === 0 ? (
            <p className="px-6 py-8 text-sm text-slate-500">
              No terms have been created for this session yet.
            </p>
          ) : (
            <div className="divide-y divide-slate-100">
              {termsQuery.data?.map((term) => (
                <div
                  key={term.id}
                  className="flex flex-col gap-4 px-6 py-5"
                >
                  {editingId === term.id ? (
                    <div className="grid gap-4 sm:grid-cols-3">
                      <div>
                        <label
                          htmlFor={`edit-term-name-${term.id}`}
                          className="mb-1.5 block text-sm font-medium text-slate-700"
                        >
                          Term
                        </label>
                        <select
                          id={`edit-term-name-${term.id}`}
                          value={editingName}
                          onChange={(event) =>
                            setEditingName(event.target.value as TermName)
                          }
                          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm"
                        >
                          {termOptions.map((option) => (
                            <option key={option} value={option}>
                              {termLabels[option]}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div>
                        <label
                          htmlFor={`edit-term-start-${term.id}`}
                          className="mb-1.5 block text-sm font-medium text-slate-700"
                        >
                          Start date
                        </label>
                        <input
                          id={`edit-term-start-${term.id}`}
                          type="date"
                          value={editingStartDate}
                          onChange={(event) =>
                            setEditingStartDate(event.target.value)
                          }
                          className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                        />
                      </div>

                      <div>
                        <label
                          htmlFor={`edit-term-end-${term.id}`}
                          className="mb-1.5 block text-sm font-medium text-slate-700"
                        >
                          End date
                        </label>
                        <input
                          id={`edit-term-end-${term.id}`}
                          type="date"
                          value={editingEndDate}
                          onChange={(event) =>
                            setEditingEndDate(event.target.value)
                          }
                          className="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm"
                        />
                      </div>

                      <div className="flex gap-2 sm:col-span-3">
                        <button
                          type="button"
                          onClick={() => saveEdit(term.id)}
                          disabled={updateMutation.isPending}
                          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50"
                        >
                          {updateMutation.isPending ? "Saving…" : "Save"}
                        </button>

                        <button
                          type="button"
                          onClick={() => setEditingId(null)}
                          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <div className="flex items-center gap-3">
                          <span className="font-medium text-slate-900">
                            {termLabels[term.name]}
                          </span>

                          {term.is_current && (
                            <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                              Current
                            </span>
                          )}
                        </div>

                        <p className="mt-1 text-sm text-slate-500">
                          {term.start_date || term.end_date
                            ? `${term.start_date ?? "No start date"} → ${
                                term.end_date ?? "No end date"
                              }`
                            : "No dates set"}
                        </p>
                      </div>

                      <button
                        type="button"
                        onClick={() =>
                          startEditing(
                            term.id,
                            term.name,
                            term.start_date,
                            term.end_date,
                          )
                        }
                        className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Edit
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
