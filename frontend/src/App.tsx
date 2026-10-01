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
import { StudentResultPage } from "@/pages/StudentResultPage";
import { TeachersPage } from "@/pages/TeachersPage";

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
            <ProtectedRoute roles={["SCHOOL_ADMIN", "SUPER_ADMIN"]}>
              <SchoolProfilePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/academic/sessions/:sessionId/terms"
          element={
            <ProtectedRoute roles={["SCHOOL_ADMIN", "SUPER_ADMIN"]}>
              <AcademicTermsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/academic/sessions"
          element={
            <ProtectedRoute roles={["SCHOOL_ADMIN", "SUPER_ADMIN"]}>
              <AcademicSessionsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/teachers"
          element={
            <ProtectedRoute roles={["SCHOOL_ADMIN", "SUPER_ADMIN"]}>
              <TeachersPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/students"
          element={
            <ProtectedRoute roles={["SCHOOL_ADMIN", "TEACHER", "SUPER_ADMIN"]}>
              <StudentsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/students/:studentId"
          element={
            <ProtectedRoute roles={["SCHOOL_ADMIN", "TEACHER", "SUPER_ADMIN"]}>
              <StudentDetailsPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/scores"
          element={
            <ProtectedRoute roles={["TEACHER", "SUPER_ADMIN"]}>
              <ScoresPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/student/results"
          element={
            <ProtectedRoute roles={["STUDENT"]}>
              <StudentResultPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
