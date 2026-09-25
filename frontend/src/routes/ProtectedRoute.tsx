import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

/**
 * Wrap any page that requires a logged-in user:
 *
 *   <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
 *
 * Redirects to /login if there's no authenticated user once the initial
 * auth check (see AuthContext's useEffect) has finished.
 */
export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-slate-500">
        Checking your session…
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
