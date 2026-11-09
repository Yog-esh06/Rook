"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Box, ExternalLink, RefreshCw } from "lucide-react";
import { api, formatDate, type Workload } from "@/lib/api";
import { PageHeader, SectionHeading, StatusPill } from "@/components/PortalShell";
import { ErrorState } from "@/components/Ui";

export default function WorkloadsPage() {
  const [items, setItems] = useState<Workload[]>([]); const [error, setError] = useState("");
  const load = () => api<Workload[]>("/api/v1/workloads").then(setItems).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read workloads"));
  useEffect(() => { load(); }, []);
  return <><PageHeader eyebrow="03 / workload explorer" title="Workload state, not guesses." description="Inspect the deployment image, replicas, pod snapshot, traffic split, and last successful observation." action={<button className="button secondary" onClick={load}><RefreshCw size={15} /> Refresh</button>} /><SectionHeading title="Tracked deployments" detail={`${items.length} workload${items.length === 1 ? "" : "s"}`} />{error ? <ErrorState message={error} retry={load} /> : <div className="panel table-wrap"><table><thead><tr><th>Workload</th><th>Image</th><th>Replicas</th><th>Traffic</th><th>Health</th><th>Last observed</th><th /></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><strong>{item.deployment_name}</strong><div className="muted">{item.namespace}</div></td><td className="mono">{item.current_image}</td><td>{item.available_replicas}/{item.desired_replicas}</td><td><span className="mono">stable {item.traffic_split.stable}%</span><div className="muted">canary {item.traffic_split.canary}%</div></td><td><StatusPill value={item.health_status} /></td><td>{formatDate(item.last_observed_at)}</td><td><Link className="inline-link" href={`/workloads/${item.id}`}><Box size={14} /> inspect</Link></td></tr>)}</tbody></table></div>}</>;
}
