import { Link } from "react-router-dom";

/**
 * Placeholder only — per Phase 4's spec, self-service school registration
 * is a Phase 5 feature. This page exists purely so the login page's
 * "Create your school account" link has somewhere honest to go, rather
 * than a dead link or (worse) a form that quietly does nothing. It does
 * NOT collect any input and does NOT create any database records.
 */
export function RegisterSchoolComingSoonPage() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
      <div className="w-full max-w-sm bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-3 text-center">
        <h1 className="text-lg font-semibold text-slate-800">School registration is coming soon</h1>
        <p className="text-sm text-slate-500">
          Self-service school sign-up isn't available yet. If your school already
          has an account, sign in below. Otherwise, check back soon.
        </p>
        <Link
          to="/login"
          className="inline-block rounded-md bg-slate-800 text-white text-sm font-medium px-4 py-2 hover:bg-slate-700"
        >
          Back to sign in
        </Link>
      </div>
    </div>
  );
}
