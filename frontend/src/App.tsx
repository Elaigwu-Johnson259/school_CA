import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { RegisterSchoolComingSoonPage } from "@/pages/RegisterSchoolComingSoonPage";

/**
 * Routing so far: login → protected dashboard → logout, plus an honest
 * "coming soon" placeholder for self-service school registration (the
 * real flow is Phase 5 — see README). The full app's routes (students,
 * classes, results, ...) get added in later phases.
 */
function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register-school" element={<RegisterSchoolComingSoonPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
