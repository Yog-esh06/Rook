"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Activity, AlertTriangle, Boxes, CheckCircle2, Clock3, Gauge, Server, ShieldCheck } from "lucide-react";
import { api, formatDate, formatPercent, type Overview, type Release } from "@/lib/api";
import { PageHeader, SectionHeading, StatusPill } from "@/components/PortalShell";
import { ErrorState, KpiCard, SignalRow } from "@/components/Ui";

function ReleaseSummary({ release }: { release: Release }) {
  return <div className="release-card">
    <div className="release-card-header"><div><h3>{release.release_version} · {release.strategy}</h3><p>{release.id.slice(0, 8)} · started {formatDate(release.started_at)}</p></div><StatusPill value={release.status} /></div>
    <div className="progress-line">{[10, 25, 50, 100].map((stage, index) => <div key={stage} className={`progress-node ${release.traffic_percentage >= stage ? "done" : index === release.current_stage_index ? "active" : ""}`}><span>{stage}</span></div>)}</div>
    <div className="progress-labels"><span>stable</span><span>{release.traffic_percentage}% canary</span><span>decision-driven</span></div>
  </div>;
}

export default function OverviewPage() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState("");
  const load = () => api<Overview>("/api/v1/overview").then(setData).catch((reason) => setError(reason instanceof Error ? reason.message : "Unable to read overview"));
  useEffect(() => { load(); const timer = setInterval(load, 2500); return () => clearInterval(timer); }, []);

  if (error && !data) return <><PageHeader eyebrow="01 / operational overview" title="Signal before assumption." description="Rook reads release state, workload health, and persisted evidence from the control plane." /><ErrorState message={error} retry={load} /></>;
  if (!data) return <div className="empty-state"><Activity size={22} /><strong>Connecting to the control plane</strong><p>Waiting for the first live read from the local gateway.</p></div>;
  return <>
    <PageHeader eyebrow="01 / operational overview" title="Signal before assumption." description="A live read of the local release control plane. Every number below is persisted or collected by the running demo." action={<Link className="button" href="/release-center">Open release center <Activity size={15} /></Link>} />
    <div className="grid kpi-grid">
      <KpiCard label="Connected clusters" value={`${data.connected_clusters}/${data.cluster_count}`} detail="cluster adapter status" tone="good" icon={<Server size={16} />} />
      <KpiCard label="Tracked workloads" value={data.workload_count} detail="deployment inventory" icon={<Boxes size={16} />} />
      <KpiCard label="Active releases" value={data.active_releases} detail="state machine in motion" tone="warn" icon={<Activity size={16} />} />
      <KpiCard label="Failed / rolled back" value={data.failed_rollouts} detail="terminal release outcomes" tone={data.failed_rollouts ? "bad" : "good"} icon={<AlertTriangle size={16} />} />
      <KpiCard label="SLO health" value={`${data.healthy_slos}/${data.total_slos}`} detail="workloads with healthy policy signals" tone="good" icon={<Gauge size={16} />} />
    </div>
    <div className="grid two">
      <section><SectionHeading title="Workload posture" detail="last control-plane observation" /><div className="panel panel-inner"><div className="signal-list">{data.workloads.map((workload) => <SignalRow key={workload.id} label={workload.deployment_name} detail={`${workload.namespace} · ${workload.current_image} · ${workload.available_replicas}/${workload.desired_replicas} ready`} value={workload.health_status} tone={workload.health_status === "HEALTHY" ? "good" : "bad"} />)}</div></div></section>
      <section><SectionHeading title="Latest decision" detail="evidence trail" /><div className="panel panel-inner">{data.latest_release ? <ReleaseSummary release={data.latest_release} /> : <div className="empty-state"><Clock3 size={20} /><strong>No release recorded</strong><p>Start the first canary from Release Center.</p></div>}{data.latest_incident && <div className="detail-cell" style={{ marginTop: 12 }}><span>Latest incident</span><strong>{data.latest_incident.recovery_status} · {data.latest_incident.severity}</strong><p className="muted" style={{ marginTop: 6, fontSize: 12 }}>{data.latest_incident.detected_condition}</p></div>}</div></section>
    </div>
    <section><SectionHeading title="What Rook proves locally" detail="current mode" /><div className="panel panel-inner"><div className="detail-grid"><div className="detail-cell"><span><ShieldCheck size={12} /> release path</span><strong>5 → 25 → 50 → 100%</strong></div><div className="detail-cell"><span><CheckCircle2 size={12} /> decision input</span><strong>requests + readiness + p95</strong></div><div className="detail-cell"><span><Activity size={12} /> traffic mechanism</span><strong>in-process gateway</strong></div><div className="detail-cell"><span><Clock3 size={12} /> last observed</span><strong>{formatDate(data.workloads[0]?.last_observed_at)}</strong></div></div></div></section>
  </>;
}
