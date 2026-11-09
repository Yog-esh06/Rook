"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, Archive, Boxes, ClipboardList, Gauge, FlaskConical, Home, Layers3, ListTree, Settings2, ShieldCheck } from "lucide-react";
import type { ReactNode } from "react";

const navigation = [
  { href: "/", label: "Overview", icon: Home },
  { href: "/applications", label: "Applications", icon: Boxes },
  { href: "/release-center", label: "Release Center", icon: Activity },
  { href: "/workloads", label: "Workload Explorer", icon: Layers3 },
  { href: "/reliability", label: "Reliability Lab", icon: FlaskConical },
  { href: "/slo", label: "SLO Explorer", icon: Gauge },
  { href: "/incidents", label: "Incident Timeline", icon: ListTree },
  { href: "/audit", label: "Audit Explorer", icon: ClipboardList },
  { href: "/settings", label: "Settings", icon: Settings2 },
];

export function PortalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link href="/" className="brand-lockup">
          <span className="brand-mark"><ShieldCheck size={19} /></span>
          <span><strong>ROOK</strong><small>release reliability</small></span>
        </Link>
        <div className="sidebar-label">Control plane</div>
        <nav className="nav-list" aria-label="Primary navigation">
          {navigation.map(({ href, label, icon: Icon }) => (
            <Link key={href} href={href} className={`nav-item ${pathname === href ? "active" : ""}`}>
              <Icon size={16} strokeWidth={1.8} />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="connection-dot"><span /> local gateway connected</div>
          <small>Evidence-first operations console</small>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <div><span className="eyebrow">ROOK / LOCAL CONTROL PLANE</span><span className="topbar-title">Release safely. Detect failure. Recover with evidence.</span></div>
          <div className="topbar-meta"><span className="status-badge good">● demo mode</span><span className="mono">operator</span></div>
        </header>
        <div className="content-wrap">{children}</div>
      </main>
    </div>
  );
}

export function PageHeader({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{description}</p></div>{action}</div>;
}

export function StatusPill({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const tone = normalized.includes("succeed") || normalized.includes("healthy") || normalized.includes("recover") || normalized === "connected" ? "good" : normalized.includes("fail") || normalized.includes("rollback") || normalized.includes("halt") || normalized.includes("degrad") ? "bad" : normalized.includes("observ") || normalized.includes("promot") || normalized.includes("running") ? "warn" : "neutral";
  return <span className={`status-badge ${tone}`}>{value.replaceAll("_", " ")}</span>;
}

export function SectionHeading({ title, detail }: { title: string; detail?: string }) {
  return <div className="section-heading"><h2>{title}</h2>{detail && <span>{detail}</span>}</div>;
}
