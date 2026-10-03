import { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMySchool, fetchMySchoolLogo } from "@/api/schools";
import { useAuth } from "@/context/AuthContext";
import type { UserRole } from "@/types/auth";

interface NavigationItem {
  label: string;
  path: string;
  icon: string;
  roles: UserRole[];
  end?: boolean;
}

const allRoles: UserRole[] = ["SCHOOL_ADMIN", "TEACHER", "SUPER_ADMIN"];
const academicLeads: UserRole[] = ["SCHOOL_ADMIN", "SUPER_ADMIN"];

const navigation: NavigationItem[] = [
  { label: "Dashboard", path: "/dashboard", icon: "dashboard", roles: ["SCHOOL_ADMIN", "TEACHER", "STUDENT", "SUPER_ADMIN"], end: true },
  { label: "Academic sessions", path: "/academic/sessions", icon: "calendar_month", roles: academicLeads },
  { label: "Teachers & assignments", path: "/teachers", icon: "co_present", roles: academicLeads },
  { label: "Students", path: "/students", icon: "groups", roles: ["SCHOOL_ADMIN", "TEACHER", "SUPER_ADMIN"] },
  { label: "Manual score entry", path: "/scores", icon: "edit_note", roles: ["TEACHER", "SUPER_ADMIN"] },
  { label: "AI marking", path: "/ai-marking", icon: "auto_awesome", roles: allRoles },
  { label: "Examinations", path: "/examinations", icon: "quiz", roles: allRoles },
  { label: "My results", path: "/student/results", icon: "workspace_premium", roles: ["STUDENT"] },
  { label: "School profile", path: "/school/profile", icon: "domain", roles: ["SCHOOL_ADMIN"] },
];

export function AcademicShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const [logoUrl, setLogoUrl] = useState("");
  const school = useQuery({
    queryKey: ["my-school"],
    queryFn: fetchMySchool,
    enabled: Boolean(user?.school_id) && user?.role !== "SUPER_ADMIN",
  });
  const items = useMemo(() => navigation.filter((item) => item.roles.includes(user?.role ?? "STUDENT")), [user?.role]);
  const activeItem = [...items].sort((left, right) => right.path.length - left.path.length).find((item) =>
    item.end ? location.pathname === item.path : location.pathname.startsWith(item.path),
  );
  const initials = (user?.email ?? roleName(user?.role)).split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0].toUpperCase()).join("");

  useEffect(() => {
    let mounted = true;
    let objectUrl = "";
    if (school.data?.logo_path) {
      fetchMySchoolLogo().then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        if (mounted) setLogoUrl(objectUrl);
      }).catch(() => { if (mounted) setLogoUrl(""); });
    } else {
      setLogoUrl("");
    }
    return () => {
      mounted = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [school.data?.logo_path]);

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <div className="academic-shell">
      <aside className="academic-sidebar" aria-label="Primary navigation">
        <NavBrand logoUrl={logoUrl} schoolName={school.data?.name} />
        <p className="academic-nav-caption">ACADEMIC WORKSPACE</p>
        <nav className="academic-nav-list">
          {items.map((item) => <NavigationLink key={item.path} item={item} onNavigate={closeMenu} />)}
        </nav>
        <div className="academic-sidebar-bottom">
          {school.data?.name && <p className="academic-tenant-name" title={school.data.name}>{school.data.name}</p>}
          <UserBlock initials={initials} role={user?.role} email={user?.email} logout={logout} />
        </div>
      </aside>

      <div className="academic-main-column">
        <header className="academic-topbar">
          <button className="academic-icon-button academic-mobile-menu" type="button" aria-label="Open navigation" aria-expanded={menuOpen} onClick={() => setMenuOpen(true)}>
            <span className="material-symbols-outlined" aria-hidden="true">menu</span>
          </button>
          <div className="academic-topbar-context">
            <span className="academic-topbar-eyebrow">{school.data?.name ?? (user?.role === "SUPER_ADMIN" ? "School_CA administration" : "Academic workspace")}</span>
            <span className="academic-topbar-title">{activeItem?.label ?? "Academic workspace"}</span>
          </div>
          <div className="academic-topbar-actions">
            <span className="academic-role-badge">{roleName(user?.role)}</span>
            <span className="academic-user-avatar" aria-label={user?.email ?? "User"}>{initials || "U"}</span>
          </div>
        </header>

        <div className="academic-page-content">{children}</div>

        <nav className="academic-bottom-nav" aria-label="Mobile navigation">
          {mobileItems(items, user?.role).map((item) => <NavigationLink key={item.path} item={item} onNavigate={closeMenu} compact />)}
          <button className="academic-mobile-nav-link" type="button" aria-label="Open full navigation" onClick={() => setMenuOpen(true)}>
            <span className="material-symbols-outlined" aria-hidden="true">more_horiz</span><span>More</span>
          </button>
        </nav>
      </div>

      {menuOpen && <div className="academic-mobile-overlay" role="presentation" onClick={closeMenu}>
        <aside className="academic-mobile-drawer" role="dialog" aria-modal="true" aria-label="Navigation menu" onClick={(event) => event.stopPropagation()}>
          <div className="academic-drawer-heading"><NavBrand logoUrl={logoUrl} schoolName={school.data?.name} /><button className="academic-icon-button" type="button" aria-label="Close navigation" onClick={closeMenu}><span className="material-symbols-outlined" aria-hidden="true">close</span></button></div>
          <nav className="academic-nav-list">{items.map((item) => <NavigationLink key={item.path} item={item} onNavigate={closeMenu} />)}</nav>
          <UserBlock initials={initials} role={user?.role} email={user?.email} logout={logout} />
        </aside>
      </div>}
    </div>
  );
}

function NavBrand({ logoUrl, schoolName }: { logoUrl: string; schoolName?: string }) {
  return <div className="academic-brand">
    <img src={logoUrl || "/brand/school-ca-mark.png"} alt="" className="academic-brand-mark" />
    <div className="academic-brand-copy"><strong>School_CA</strong><span>{schoolName ?? "Academic platform"}</span></div>
  </div>;
}

function NavigationLink({ item, onNavigate, compact = false }: { item: NavigationItem; onNavigate: () => void; compact?: boolean }) {
  return <NavLink to={item.path} end={item.end} onClick={onNavigate} className={({ isActive }) => `${compact ? "academic-mobile-nav-link" : "academic-nav-link"}${isActive ? " is-active" : ""}`}>
    <span className="material-symbols-outlined" aria-hidden="true">{item.icon}</span><span>{item.label}</span>
  </NavLink>;
}

function UserBlock({ initials, role, email, logout }: { initials: string; role?: UserRole; email: string | null | undefined; logout: () => Promise<void> }) {
  return <div className="academic-user-block">
    <span className="academic-user-avatar" aria-hidden="true">{initials || "U"}</span>
    <div className="academic-user-meta"><strong>{roleName(role)}</strong><span title={email ?? ""}>{email ?? "System administrator"}</span></div>
    <button type="button" className="academic-icon-button" aria-label="Sign out" title="Sign out" onClick={() => void logout()}><span className="material-symbols-outlined" aria-hidden="true">logout</span></button>
  </div>;
}

function mobileItems(items: NavigationItem[], role?: UserRole) {
  if (role === "STUDENT") return items.filter((item) => ["/dashboard", "/student/results"].includes(item.path));
  const preferred = role === "TEACHER"
    ? ["/dashboard", "/students", "/ai-marking", "/scores"]
    : ["/dashboard", "/students", "/teachers", "/ai-marking"];
  return items.filter((item) => preferred.includes(item.path)).slice(0, 4);
}

function roleName(role?: UserRole) {
  switch (role) {
    case "TEACHER": return "Teacher";
    case "SCHOOL_ADMIN": return "School admin";
    case "STUDENT": return "Student";
    case "SUPER_ADMIN": return "Super admin";
    default: return "Signed in";
  }
}
