import { AlertTriangle, ArrowUpRight, CheckCircle2, CircleSlash2, Clock3, Database, RadioTower } from "lucide-react";
import type { ReactNode } from "react";

export function KpiCard({ label, value, detail, tone = "neutral", icon }: { label: string; value: string | number; detail: string; tone?: string; icon?: ReactNode }) {
  return <div className={`kpi-card tone-${tone}`}><div className="kpi-top"><span>{label}</span><span className="kpi-icon">{icon}</span></div><strong>{value}</strong><small>{detail}</small></div>;
}

export function EmptyState({ title, detail, action }: { title: string; detail: string; action?: ReactNode }) {
  return <div className="empty-state"><CircleSlash2 size={22} /><strong>{title}</strong><p>{detail}</p>{action}</div>;
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error-state"><AlertTriangle size={20} /><div><strong>Control plane unavailable</strong><p>{message}</p>{retry && <button className="button subtle" onClick={retry}>Retry read</button>}</div></div>;
}

export function SignalRow({ label, value, detail, tone = "neutral" }: { label: string; value: string; detail: string; tone?: string }) {
  return <div className="signal-row"><div className={`signal-icon ${tone}`}><RadioTower size={15} /></div><div><strong>{label}</strong><span>{detail}</span></div><b>{value}</b></div>;
}

export function MiniLink({ href, children }: { href: string; children: ReactNode }) {
  return <a className="inline-link" href={href}>{children}<ArrowUpRight size={14} /></a>;
}

export const iconSet = { clock: <Clock3 size={16} />, database: <Database size={16} />, check: <CheckCircle2 size={16} /> };
