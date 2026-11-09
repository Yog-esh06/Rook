"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Box, RotateCw, Server } from "lucide-react";
import { api, formatDate, type Workload } from "@/lib/api";
import { PageHeader, SectionHeading, StatusPill } from "@/components/PortalShell";
import { ErrorState } from "@/components/Ui";

export default function WorkloadDetailPage() {
  const params = useParams<{ id: string }>(); const [item, setItem] = useState<Workload | null>(null); const [error, setError] = useState("");
  const load = () => api<Workload>(`/api/v1/workloads/${params.id}`).then(setItem).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read workload"));
  useEffect(() => { if (params.id) load(); }, [params.id]);
  return <>{error ? <ErrorState message={error} retry={load} /> : item ? <><PageHeader eyebrow="03 / workload explorer" title={item.deployment_name} description={`${item.namespace} · source of truth is the live workload adapter, with Rook evidence layered around it.`} action={<button className="button secondary" onClick={load}><RotateCw size={15} /> Re-read state</button>} /><div className="detail-grid"><div className="detail-cell"><span>image</span><strong className="mono">{item.current_image}</strong></div><div className="detail-cell"><span>version</span><strong>{item.current_version}</strong></div><div className="detail-cell"><span>replicas</span><strong>{item.available_replicas}/{item.desired_replicas}</strong></div><div className="detail-cell"><span>status</span><strong><StatusPill value={item.health_status} /></strong></div></div><div className="grid two"><section><SectionHeading title="Pod snapshot" detail="latest persisted read" /><div className="panel panel-inner"><div className="signal-list">{item.pod_snapshot.map((pod) => <div className="signal-row" key={pod.name}><div className="signal-icon good"><Server size={15} /></div><div><strong>{pod.name}</strong><span>{pod.image} · restarts {pod.restarts}</span></div><b>{pod.ready ? "ready" : "not ready"}</b></div>)}</div></div></section><section><SectionHeading title="Traffic route" detail="gateway split" /><div className="panel panel-inner"><div className="detail-grid"><div className="detail-cell"><span>stable</span><strong>{item.traffic_split.stable}%</strong></div><div className="detail-cell"><span>canary</span><strong>{item.traffic_split.canary}%</strong></div></div><p className="muted" style={{ marginTop: 16, fontSize: 12, lineHeight: 1.6 }}>Local demo mode routes actual requests through the in-process gateway. Kubernetes mode uses the adapter boundary documented in the repository.</p><p className="muted" style={{ marginTop: 12, fontSize: 11 }}>Last observed: {formatDate(item.last_observed_at)}</p></div></section></div></> : <div className="empty-state"><Box size={22} /><strong>Reading workload</strong><p>Waiting for the control plane response.</p></div>}</>;
}
