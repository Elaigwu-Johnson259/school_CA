import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { RegisterSchoolPage } from "@/pages/RegisterSchoolPage";
import { SchoolProfilePage } from "@/pages/SchoolProfilePage";

/**
 * Routing so far: login → protected dashboard → logout, public school
 * registration, and an authenticated school-profile page. The full app's
 * routes (students, classes, results, ...) get added in later phases.
 */
function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register-school" element={<RegisterSchoolPage />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/school/profile"
          element={
            <ProtectedRoute>
              <SchoolProfilePage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
