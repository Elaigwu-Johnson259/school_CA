import { useEffect, useState } from "react";
import { checkHealth } from "@/api/health";

/**
 * Temporary placeholder App.
 *
 * This exists only to prove the frontend can talk to the backend during
 * Phase 1. Real routing (pages for login, dashboard, students, etc.) gets
 * built out in later phases inside src/routes and src/pages.
 */
function App() {
  const [status, setStatus] = useState<"checking" | "ok" | "error">(
    "checking"
  );

  useEffect(() => {
    checkHealth()
      .then(() => setStatus("ok"))
      .catch(() => setStatus("error"));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-semibold text-slate-800">
          School Results Management System
        </h1>
        <p className="text-slate-500">Phase 1 scaffold is running.</p>
        <p className="text-sm text-slate-400">
          Backend health check:{" "}
          <span
            className={
              status === "ok"
                ? "text-green-600"
                : status === "error"
                ? "text-red-600"
                : "text-slate-400"
            }
          >
            {status}
          </span>
        </p>
      </div>
    </div>
  );
}

export default App;
