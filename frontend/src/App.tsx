import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { RegisterSchoolPage } from "@/pages/RegisterSchoolPage";
import { SchoolProfilePage } from "@/pages/SchoolProfilePage";
import { AcademicSessionsPage } from "@/pages/AcademicSessionsPage";
import { AcademicTermsPage } from "@/pages/AcademicTermsPage";
import { StudentsPage } from "@/pages/StudentsPage";
import { StudentDetailsPage } from "@/pages/StudentDetailsPage";
import { ScoresPage } from "@/pages/ScoresPage";

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
        <Route
          path="/academic/sessions/:sessionId/terms"
          element={
            <ProtectedRoute>
              <AcademicTermsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/academic/sessions"
          element={
            <ProtectedRoute>
              <AcademicSessionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/students"
          element={
            <ProtectedRoute>
              <StudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/students/:studentId"
          element={
            <ProtectedRoute>
              <StudentDetailsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scores"
          element={
            <ProtectedRoute>
              <ScoresPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
