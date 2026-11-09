"use client";

import { useEffect, useState } from "react";
import { ClipboardList, Search } from "lucide-react";
import { api, formatDate } from "@/lib/api";
import { PageHeader, SectionHeading } from "@/components/PortalShell";
import { EmptyState, ErrorState } from "@/components/Ui";

type Audit = { id: string; actor: string; action: string; resource: string; request_id: string | null; metadata_json: Record<string, unknown>; created_at: string };

export default function AuditPage() {
  const [items, setItems] = useState<Audit[]>([]); const [filter, setFilter] = useState(""); const [error, setError] = useState("");
  useEffect(() => { api<Audit[]>(`/api/v1/audit${filter ? `?action=${encodeURIComponent(filter)}` : ""}`).then(setItems).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read audit history")); }, [filter]);
  return <><PageHeader eyebrow="08 / audit explorer" title="Audit history with context." description="Every release transition, observation, experiment, halt, and recovery is written as a structured event with actor and resource correlation." /><SectionHeading title="Event stream" detail={`${items.length} records`} />{error ? <ErrorState message={error} /> : <><div className="panel panel-inner" style={{ marginBottom: 12 }}><div className="field"><label><Search size={12} /> filter by action</label><input value={filter} onChange={(event) => setFilter(event.target.value)} placeholder="release.observation" /></div></div>{items.length === 0 ? <EmptyState title="No audit events" detail="Events appear after the control plane seeds data or a release runs." /> : <div className="panel table-wrap"><table><thead><tr><th>Timestamp</th><th>Action</th><th>Actor</th><th>Resource</th><th>Metadata</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{formatDate(item.created_at)}</td><td><strong>{item.action}</strong></td><td>{item.actor}</td><td className="mono">{item.resource}</td><td className="mono">{JSON.stringify(item.metadata_json)}</td></tr>)}</tbody></table></div>}</>}</>;
}
