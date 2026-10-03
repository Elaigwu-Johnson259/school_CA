import { useEffect, useState, type FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { fetchMySchool, fetchMySchoolLogo, updateMySchool, uploadMySchoolLogo } from "@/api/schools";
import type { SchoolUpdateRequest } from "@/types/schoolRegistration";

const EDITABLE_FIELDS: Array<{ key: keyof SchoolUpdateRequest; label: string }> = [
  { key: "name", label: "School name" },
  { key: "email", label: "School email" },
  { key: "phone", label: "Phone" },
  { key: "address", label: "Address" },
  { key: "state", label: "State" },
  { key: "country", label: "Country" },
  { key: "motto", label: "Motto" },
  { key: "website", label: "Website" },
  { key: "principal_name", label: "Principal / head teacher" },
];

/**
 * Authenticated school profile page. SCHOOL_ADMIN can view and edit;
 * the backend (not this page) is what actually enforces that — a
 * TEACHER/STUDENT hitting PATCH /api/schools/me gets a 403 regardless of
 * what this page shows or hides.
 */
export function SchoolProfilePage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const isSchoolAdmin = user?.role === "SCHOOL_ADMIN";

  const { data: school, isLoading } = useQuery({
    queryKey: ["my-school"],
    queryFn: fetchMySchool,
    enabled: user?.school_id !== null && user?.school_id !== undefined,
  });

  const [form, setForm] = useState<SchoolUpdateRequest>({});
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState("");

  useEffect(() => {
    if (school) {
      setForm({
        name: school.name,
        email: school.email,
        phone: school.phone ?? "",
        address: school.address ?? "",
        state: school.state ?? "",
        country: school.country ?? "",
        motto: school.motto ?? "",
        website: school.website ?? "",
        principal_name: school.principal_name ?? "",
      });
    }
  }, [school]);

  useEffect(() => {
    let objectUrl = "";
    if (school?.logo_path) {
      fetchMySchoolLogo().then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setLogoPreview(objectUrl);
      }).catch(() => setLogoPreview(""));
    } else {
      setLogoPreview("");
    }
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [school?.logo_path]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSaveError(null);
    setSaveMessage(null);
    setIsSaving(true);
    try {
      const updated = await updateMySchool(form);
      queryClient.setQueryData(["my-school"], updated);
      setSaveMessage("School profile updated.");
    } catch {
      setSaveError("Couldn't save your changes. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogoUpload() {
    if (!logoFile) return;
    setSaveError(null);
    setSaveMessage(null);
    try {
      const updated = await uploadMySchoolLogo(logoFile);
      queryClient.setQueryData(["my-school"], updated);
      setLogoFile(null);
      setSaveMessage("School logo updated.");
    } catch (error: any) {
      setSaveError(error?.response?.data?.detail ?? "Couldn't upload the school logo.");
    }
  }

  if (user?.role === "SUPER_ADMIN") {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-2 text-center">
          <p className="text-sm text-slate-500">
            Super Administrators aren't tied to a single school, so there's no
            profile page to show here.
          </p>
          <Link to="/dashboard" className="text-sm font-medium text-slate-700 hover:underline">
            Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-lg bg-white rounded-lg shadow-sm border border-slate-200 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-slate-800">School profile</h1>
          <Link to="/dashboard" className="text-sm text-slate-500 hover:underline">
            Back to dashboard
          </Link>
        </div>

        {isLoading && <p className="text-sm text-slate-400">Loading…</p>}

        {school && (
          <form onSubmit={handleSubmit} className="space-y-3">
            <section className="rounded-md border border-slate-200 p-3">
              <p className="text-sm font-medium text-slate-700">School logo</p>
              {logoPreview && <img src={logoPreview} alt={`${school.name} logo`} className="mt-2 h-16 max-w-48 object-contain" />}
              {isSchoolAdmin && <><input type="file" accept="image/png,image/jpeg" onChange={(event) => setLogoFile(event.target.files?.[0] ?? null)} className="mt-2 block w-full text-sm" /><button type="button" disabled={!logoFile} onClick={handleLogoUpload} className="mt-2 rounded-md border border-slate-300 px-3 py-2 text-sm disabled:opacity-50">Upload logo</button></>}
            </section>
            {EDITABLE_FIELDS.map(({ key, label }) => (
              <div key={key} className="space-y-1">
                <label htmlFor={key} className="text-sm font-medium text-slate-700">
                  {label}
                </label>
                <input
                  id={key}
                  value={form[key] ?? ""}
                  disabled={!isSchoolAdmin}
                  onChange={(e) => setForm((prev) => ({ ...prev, [key]: e.target.value }))}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:bg-slate-50 disabled:text-slate-500"
                />
              </div>
            ))}

            {!isSchoolAdmin && (
              <p className="text-sm text-slate-400">
                Only a School Administrator can edit this profile.
              </p>
            )}
            {saveError && <p className="text-sm text-red-600">{saveError}</p>}
            {saveMessage && <p className="text-sm text-green-600">{saveMessage}</p>}

            {isSchoolAdmin && (
              <button
                type="submit"
                disabled={isSaving}
                className="w-full rounded-md bg-slate-800 text-white text-sm font-medium py-2 hover:bg-slate-700 disabled:opacity-50"
              >
                {isSaving ? "Saving…" : "Save changes"}
              </button>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
