export type Workload = {
  id: string;
  application_id: string;
  cluster_id: string;
  namespace: string;
  deployment_name: string;
  current_image: string;
  current_version: string;
  desired_replicas: number;
  available_replicas: number;
  health_status: string;
  traffic_split: { stable: number; canary: number };
  pod_snapshot: Array<{ name: string; image: string; ready: boolean; restarts: number }>;
  last_observed_at: string | null;
};

export type ApplicationResponse = {
  id: string;
  name: string;
  slug: string;
  repository_url: string | null;
  owner: string;
  created_at: string;
};

export type Release = {
  id: string;
  workload_id: string;
  release_version: string;
  image_reference: string;
  previous_version: string | null;
  previous_image: string | null;
  strategy: string;
  status: string;
  failure_mode: string | null;
  created_by: string;
  current_stage_index: number;
  traffic_percentage: number;
  started_at: string;
  completed_at: string | null;
  last_error: string | null;
};

export type RolloutStep = {
  id: string;
  release_id: string;
  step_number: number;
  target_traffic_percentage: number;
  observed_error_rate: number | null;
  observed_p95_latency_ms: number | null;
  readiness_status: boolean | null;
  request_sample_count: number;
  restart_count: number | null;
  resource_pressure: number | null;
  telemetry_available: boolean;
  telemetry_observed_at: string | null;
  decision: string;
  decision_reason: string;
  latency_samples_ms: number[];
  observed_at: string;
};

export type ReleaseDetail = Release & { steps: RolloutStep[] };

export type Incident = {
  id: string;
  release_id: string;
  severity: string;
  detected_condition: string;
  timeline: Array<{ timestamp: string; kind: string; message: string; metadata: Record<string, unknown> }>;
  recovery_status: string;
  created_at: string;
};

export type Overview = {
  cluster_count: number;
  connected_clusters: number;
  workload_count: number;
  active_releases: number;
  failed_rollouts: number;
  open_incidents: number;
  healthy_slos: number;
  total_slos: number;
  latest_release: Release | null;
  latest_incident: Incident | null;
  workloads: Workload[];
};

export type SLOPolicy = {
  id: string;
  workload_id: string;
  name: string;
  availability_target: number;
  error_threshold: number;
  latency_threshold_ms: number;
  readiness_target: number;
  minimum_sample_count: number;
  observation_window_seconds: number;
  max_restart_count: number;
  max_resource_pressure: number;
};

export type ExperimentRun = {
  id: string;
  release_id: string;
  experiment_type: string;
  status: string;
  configuration: Record<string, unknown>;
  result: Record<string, unknown>;
  started_at: string;
  completed_at: string | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export function apiBase() {
  return API_BASE;
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "Not observed";
  return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

export function formatPercent(value: number | null | undefined) {
  return value == null ? "Unavailable" : `${(value * 100).toFixed(2)}%`;
}
