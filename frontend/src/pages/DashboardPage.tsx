import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/context/AuthContext";
import { fetchMySchool } from "@/api/schools";
import { roleLabel } from "@/utils/roleLabels";

/**
 * Minimal placeholder proving the authenticated + tenant-aware flow
 * works end to end. The real per-role dashboards get built in a later
 * phase — this only shows enough (school name, user email, human-readable
 * role) to confirm the account/tenant identity a logged-in user is
 * operating as, per Phase 4's UX requirements.
 */
export function DashboardPage() {
  const { user, logout } = useAuth();

  // SUPER_ADMIN has no single "home" school (school_id is null) — never
  // fabricate one for them. Only ask for a school when the logged-in
  // user actually belongs to one.
  const isSchoolBound = user?.school_id !== null && user?.school_id !== undefined;

  const { data: school, isLoading: isSchoolLoading } = useQuery({
    queryKey: ["my-school"],
    queryFn: fetchMySchool,
    enabled: isSchoolBound,
  });

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-4 text-center">
        <p className="text-sm text-slate-400">Welcome back</p>

        {isSchoolBound ? (
          <div>
            {isSchoolLoading && <p className="text-sm text-slate-400">Loading school…</p>}
            {school && (
              <h1 className="text-xl font-semibold text-slate-800">{school.name}</h1>
            )}
          </div>
        ) : (
          user && (
            <div className="space-y-1">
              <h1 className="text-xl font-semibold text-slate-800">School Results Management</h1>
              <span className="inline-block rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                Global Administration
              </span>
            </div>
          )
        )}

        {user && (
          <div className="text-sm text-slate-600 space-y-1">
            <p>{user.email}</p>
            <p className="text-slate-400">{roleLabel(user.role)}</p>
          </div>
        )}

        <button
          onClick={() => logout()}
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Log out
        </button>
      </div>
    </div>
  );
}
