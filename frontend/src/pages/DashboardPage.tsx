import { useAuth } from "@/context/AuthContext";

/**
 * Minimal placeholder proving the authenticated flow works end to end.
 * The real dashboards (per role) get built in a later phase.
 */
export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-4 text-center">
        <h1 className="text-xl font-semibold text-slate-800">You're logged in</h1>
        {user && (
          <div className="text-sm text-slate-600 space-y-1">
            <p>{user.email}</p>
            <p className="text-slate-400">
              {user.role}
              {user.school_id !== null ? ` · school #${user.school_id}` : ""}
            </p>
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
