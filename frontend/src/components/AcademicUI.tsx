import type { ReactNode } from "react";

export function PageHeading({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <header className="academic-page-heading">
    <div className="academic-page-heading-copy">
      {eyebrow && <p className="academic-eyebrow">{eyebrow}</p>}
      <h1>{title}</h1>
      {description && <p className="academic-page-description">{description}</p>}
    </div>
    {actions && <div className="academic-page-actions">{actions}</div>}
  </header>;
}

export function MetricTile({ label, value, detail, icon, tone = "blue" }: { label: string; value: string | number; detail?: string; icon: string; tone?: "blue" | "green" | "amber" | "red" }) {
  return <section className={`academic-metric-tile tone-${tone}`}>
    <div className="academic-metric-top"><span>{label}</span><span className="material-symbols-outlined" aria-hidden="true">{icon}</span></div>
    <strong>{value}</strong>
    {detail && <small>{detail}</small>}
  </section>;
}

export function StatusBadge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "danger" | "info" }) {
  return <span className={`academic-status-badge tone-${tone}`}><span className="academic-status-dot" aria-hidden="true" />{children}</span>;
}

export function Notice({ children, tone = "info", icon = "info" }: { children: ReactNode; tone?: "info" | "success" | "warning" | "danger"; icon?: string }) {
  return <div className={`academic-notice tone-${tone}`} role={tone === "danger" ? "alert" : "status"}>
    <span className="material-symbols-outlined" aria-hidden="true">{icon}</span><div>{children}</div>
  </div>;
}
