"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, ListTree } from "lucide-react";
import { api, formatDate, type Incident } from "@/lib/api";
import { PageHeader, SectionHeading, StatusPill } from "@/components/PortalShell";
import { EmptyState, ErrorState } from "@/components/Ui";

export default function IncidentsPage() {
  const [items, setItems] = useState<Incident[]>([]); const [error, setError] = useState("");
  const load = () => api<Incident[]>("/api/v1/incidents").then(setItems).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read incidents"));
  useEffect(() => { load(); const timer = setInterval(load, 1800); return () => clearInterval(timer); }, []);
  return <><PageHeader eyebrow="07 / incident evidence" title="Incident Timeline." description="Chronological evidence for the decision that stopped a rollout, the action that restored stable traffic, and the verification that followed." />{error ? <ErrorState message={error} retry={load} /> : items.length === 0 ? <EmptyState title="No incidents recorded" detail="A failed canary or controlled experiment will create an incident timeline." /> : <div className="grid">{items.map((incident) => <article className="panel panel-inner" key={incident.id}><div className="release-card-header"><div><h3><AlertTriangle size={16} style={{ verticalAlign: "middle", color: "var(--red)" }} /> {incident.detected_condition}</h3><p>{incident.id.slice(0, 8)} · created {formatDate(incident.created_at)}</p></div><StatusPill value={incident.recovery_status} /></div><div className="timeline" style={{ marginTop: 18 }}>{incident.timeline.map((event) => <div className="timeline-item" key={`${event.timestamp}-${event.kind}`}><div className="timeline-dot">{event.kind === "recovered" ? <CheckCircle2 size={12} /> : <ListTree size={12} />}</div><div><time>{formatDate(event.timestamp)} · {event.kind}</time><strong>{event.message}</strong><p>{Object.keys(event.metadata).length ? JSON.stringify(event.metadata) : "Recorded by the release service."}</p></div></div>)}</div></article>)}</div>}</>;
}
