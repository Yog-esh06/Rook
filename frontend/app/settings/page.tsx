"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, LockKeyhole, ServerCog, Settings2 } from "lucide-react";
import { api } from "@/lib/api";
import { PageHeader, SectionHeading, StatusPill } from "@/components/PortalShell";
import { ErrorState } from "@/components/Ui";

type Settings = { environment: string; demo_mode: boolean; rollout_stages: number[]; observation_seconds: number; sample_count: number; auth_enabled: boolean };

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null); const [error, setError] = useState("");
  useEffect(() => { api<Settings>("/api/v1/settings").then(setSettings).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read settings")); }, []);
  return <><PageHeader eyebrow="09 / control plane settings" title="Settings and boundaries." description="The local demo exposes its active configuration so the evidence in the console is interpretable. Production credentials never enter ordinary release records." />{error ? <ErrorState message={error} /> : settings ? <><div className="grid two"><section><SectionHeading title="Runtime" detail="read-only in local mode" /><div className="panel panel-inner"><div className="signal-list"><div className="signal-row"><div className="signal-icon good"><ServerCog size={15} /></div><div><strong>Environment</strong><span>active runtime profile</span></div><b>{settings.environment}</b></div><div className="signal-row"><div className="signal-icon good"><Settings2 size={15} /></div><div><strong>Mode</strong><span>local traffic gateway and SQLite persistence</span></div><b>{settings.demo_mode ? "demo" : "managed"}</b></div><div className="signal-row"><div className="signal-icon good"><LockKeyhole size={15} /></div><div><strong>Authentication</strong><span>role header gate is disabled for local preview</span></div><b>{settings.auth_enabled ? "enabled" : "local bypass"}</b></div></div></div></section><section><SectionHeading title="Rollout policy" detail="actual evaluator inputs" /><div className="panel panel-inner"><div className="detail-grid"><div className="detail-cell"><span>stages</span><strong>{settings.rollout_stages.join(" → ")}%</strong></div><div className="detail-cell"><span>observation</span><strong>{settings.observation_seconds}s</strong></div><div className="detail-cell"><span>sample target</span><strong>{settings.sample_count}</strong></div><div className="detail-cell"><span>telemetry</span><strong><StatusPill value="available" /></strong></div></div><div className="detail-cell" style={{ marginTop: 12 }}><span><CheckCircle2 size={12} /> policy note</span><strong>Missing, stale, or undersampled telemetry cannot promote a release.</strong></div></div></section></div></> : <div className="empty-state"><Settings2 size={22} /><strong>Reading settings</strong><p>Waiting for the control plane.</p></div>}</>;
}
