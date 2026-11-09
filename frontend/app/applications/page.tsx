"use client";

import { useEffect, useState } from "react";
import { Boxes, GitBranch, UserRound } from "lucide-react";
import { api, type ApplicationResponse, type Workload } from "@/lib/api";
import { PageHeader, SectionHeading } from "@/components/PortalShell";
import { ErrorState, EmptyState } from "@/components/Ui";

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [workloads, setWorkloads] = useState<Workload[]>([]);
  const [error, setError] = useState("");
  useEffect(() => { Promise.all([api<ApplicationResponse[]>("/api/v1/applications"), api<Workload[]>("/api/v1/workloads")]).then(([apps, items]) => { setApplications(apps); setWorkloads(items); }).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read applications")); }, []);
  return <><PageHeader eyebrow="02 / application catalog" title="Applications and workloads." description="A compact inventory of services, owners, images, and the workloads they anchor." />{error ? <ErrorState message={error} /> : <><SectionHeading title="Registered applications" detail={`${applications.length} application${applications.length === 1 ? "" : "s"}`} /><div className="grid two">{applications.map((application) => { const attached = workloads.filter((item) => item.application_id === application.id); return <article className="panel panel-inner" key={application.id}><div className="release-card-header"><div><h3>{application.name}</h3><p>{application.slug} · created {new Date(application.created_at).toLocaleDateString()}</p></div><span className="status-badge good">tracked</span></div><div className="detail-grid" style={{ marginTop: 18 }}><div className="detail-cell"><span><UserRound size={12} /> owner</span><strong>{application.owner}</strong></div><div className="detail-cell"><span><GitBranch size={12} /> repository</span><strong>{application.repository_url ? "linked" : "not linked"}</strong></div><div className="detail-cell"><span><Boxes size={12} /> workloads</span><strong>{attached.length}</strong></div><div className="detail-cell"><span>catalog id</span><strong className="mono">{application.id.slice(0, 8)}</strong></div></div>{attached.length > 0 && <div style={{ marginTop: 16 }} className="signal-list">{attached.map((workload) => <div key={workload.id} className="signal-row"><div className="signal-icon good"><Boxes size={15} /></div><div><strong>{workload.deployment_name}</strong><span>{workload.namespace} · {workload.current_version}</span></div><b>{workload.health_status}</b></div>)}</div>}</article>; })}</div>{applications.length === 0 && <EmptyState title="No applications" detail="The demo seed runs when the control plane starts." />}</>}</>;
}
