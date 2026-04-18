export interface Alert {
  id: number;
  service: string;
  exception_type: string;
  signature: string;
  severity: string;
  status: string;
  event_count: number;
  first_seen: string;
  last_seen: string;
  detected_at: string;
  resolved_at: string | null;
  fault_injected_at?: string | null;
  events?: AlertEvent[];
}

export interface AlertEvent {
  id: number;
  message: string;
  stack_trace: string;
  created_at: string;
}

export interface Diagnosis {
  id: number;
  alert_id: number;
  root_cause: string;
  contributing_factors: string[];
  confidence: number;
  latency_ms: number;
  created_at: string;
}

export interface Remediation {
  id: number;
  alert_id: number;
  target_file: string;
  diff: string;
  rationale: string;
  status: string;
  created_at: string;
  applied_at: string | null;
}

export interface Metrics {
  total_alerts: number;
  resolved_alerts: number;
  applied_remediations: number;
  avg_detection_latency_s: number | null;
  avg_diagnosis_latency_ms: number | null;
  avg_mttr_s: number | null;
}

async function json<T>(r: Response): Promise<T> {
  if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
  return r.json();
}

export const api = {
  listAlerts: () => fetch("/api/alerts").then(json<Alert[]>),
  getAlert: (id: number) => fetch(`/api/alerts/${id}`).then(json<Alert>),
  metrics: () => fetch("/api/metrics").then(json<Metrics>),
  diagnose: (id: number) =>
    fetch(`/api/alerts/${id}/diagnose`, { method: "POST" }).then(json<Diagnosis>),
  getDiagnosis: (id: number) =>
    fetch(`/api/alerts/${id}/diagnosis`).then((r) =>
      r.status === 404 ? null : json<Diagnosis>(r)
    ),
  remediate: (id: number) =>
    fetch(`/api/alerts/${id}/remediate`, { method: "POST" }).then(json<Remediation>),
  getRemediation: (id: number) =>
    fetch(`/api/alerts/${id}/remediation`).then((r) =>
      r.status === 404 ? null : json<Remediation>(r)
    ),
  approve: (remediationId: number) =>
    fetch(`/api/remediations/${remediationId}/approve`, { method: "POST" }).then(
      json<Remediation>
    ),
  reject: (remediationId: number) =>
    fetch(`/api/remediations/${remediationId}/reject`, { method: "POST" }).then(
      json<Remediation>
    ),
};
