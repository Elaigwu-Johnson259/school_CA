import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import axios from "axios";
import { registerSchool } from "@/api/schools";

/**
 * Public "create your school account" flow: collects school info + the
 * first administrator's credentials, calls POST /api/schools/register,
 * then sends the admin to /login to sign in normally — this page never
 * logs anyone in itself (the backend doesn't issue tokens from this
 * endpoint on purpose; see backend/app/api/schools.py).
 *
 * Frontend validation here (required fields, email format, password
 * confirmation, minimum length) is UX only — the backend re-validates
 * everything and is the actual authority.
 */
export function RegisterSchoolPage() {
  const navigate = useNavigate();

  const [schoolName, setSchoolName] = useState("");
  const [schoolEmail, setSchoolEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [state, setState] = useState("");
  const [country, setCountry] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  function validate(): string | null {
    if (!schoolName.trim() || !schoolEmail.trim() || !adminEmail.trim() || !password) {
      return "Please fill in all required fields.";
    }
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(schoolEmail) || !emailPattern.test(adminEmail)) {
      return "Please enter valid email addresses.";
    }
    if (password.length < 8) {
      return "Password must be at least 8 characters long.";
    }
    if (password !== confirmPassword) {
      return "Passwords do not match.";
    }
    return null;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    const validationError = validate();
    if (validationError) {
      setFormError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await registerSchool({
        school_name: schoolName.trim(),
        school_email: schoolEmail.trim(),
        phone: phone.trim() || undefined,
        address: address.trim() || undefined,
        state: state.trim() || undefined,
        country: country.trim() || undefined,
        admin_email: adminEmail.trim(),
        password,
      });
      setSuccessMessage(response.message);
      setTimeout(() => navigate("/login"), 1800);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const status = error.response?.status;
        const detail = error.response?.data?.detail;
        if (status === 409) {
          setFormError(
            typeof detail === "string"
              ? detail
              : "That school or administrator email is already registered."
          );
        } else if (status === 422) {
          setFormError("Please check the form — some fields aren't valid.");
        } else {
          setFormError("Something went wrong. Please try again.");
        }
      } else {
        setFormError("Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (successMessage) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-3 text-center">
          <h1 className="text-lg font-semibold text-slate-800">{successMessage}</h1>
          <p className="text-sm text-slate-500">Taking you to sign in…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-lg bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-6"
      >
        <div className="text-center space-y-1">
          <h1 className="text-xl font-semibold tracking-tight text-slate-800">
            Create your school account
          </h1>
          <p className="text-sm text-slate-500">
            This creates your school's workspace and its first administrator account.
          </p>
        </div>

        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-slate-700 mb-1">School information</legend>

          <div className="space-y-1">
            <label htmlFor="schoolName" className="text-sm font-medium text-slate-700">
              School name
            </label>
            <input
              id="schoolName"
              required
              value={schoolName}
              onChange={(e) => setSchoolName(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="schoolEmail" className="text-sm font-medium text-slate-700">
              School email
            </label>
            <input
              id="schoolEmail"
              type="email"
              required
              value={schoolEmail}
              onChange={(e) => setSchoolEmail(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label htmlFor="phone" className="text-sm font-medium text-slate-700">
                Phone
              </label>
              <input
                id="phone"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="state" className="text-sm font-medium text-slate-700">
                State
              </label>
              <input
                id="state"
                value={state}
                onChange={(e) => setState(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="address" className="text-sm font-medium text-slate-700">
              Address
            </label>
            <input
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="country" className="text-sm font-medium text-slate-700">
              Country
            </label>
            <input
              id="country"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
        </fieldset>

        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-slate-700 mb-1">Administrator account</legend>

          <div className="space-y-1">
            <label htmlFor="adminEmail" className="text-sm font-medium text-slate-700">
              Administrator email
            </label>
            <input
              id="adminEmail"
              type="email"
              required
              value={adminEmail}
              onChange={(e) => setAdminEmail(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="password" className="text-sm font-medium text-slate-700">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>

          <div className="space-y-1">
            <label htmlFor="confirmPassword" className="text-sm font-medium text-slate-700">
              Confirm password
            </label>
            <input
              id="confirmPassword"
              type="password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400"
            />
          </div>
        </fieldset>

        {formError && <p className="text-sm text-red-600">{formError}</p>}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-md bg-slate-800 text-white text-sm font-medium py-2 hover:bg-slate-700 disabled:opacity-50"
        >
          {isSubmitting ? "Creating account…" : "Create school account"}
        </button>

        <p className="text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-slate-700 hover:underline">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  );
}
