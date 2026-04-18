import { Route, Routes, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import AlertDashboard from "./pages/AlertDashboard";
import InvestigationView from "./pages/InvestigationView";
import DiagnosisPanel from "./pages/DiagnosisPanel";
import RemediationPanel from "./pages/RemediationPanel";
import ApprovalScreen from "./pages/ApprovalScreen";
import { api, Metrics } from "./api";

export default function App() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  useEffect(() => {
    const load = () => api.metrics().then(setMetrics).catch(() => {});
    load();
    const id = setInterval(load, 3000);
    return () => clearInterval(id);
  }, []);

  const fmt = (v: number | null | undefined, unit: string) =>
    v == null ? "—" : `${v}${unit}`;

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>AI DevOps Agent</h1>
        <nav style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 24 }}>
          <Link to="/">Alerts</Link>
        </nav>
        <h3 style={{ fontSize: 12, color: "#9aa5b1", marginBottom: 8 }}>KPIs</h3>
        <div className="metric">
          Total alerts <b>{metrics?.total_alerts ?? 0}</b>
        </div>
        <div className="metric">
          Resolved <b>{metrics?.resolved_alerts ?? 0}</b>
        </div>
        <div className="metric">
          Fixes applied <b>{metrics?.applied_remediations ?? 0}</b>
        </div>
        <div className="metric">
          Detection latency <b>{fmt(metrics?.avg_detection_latency_s, "s")}</b>
        </div>
        <div className="metric">
          Diagnosis latency <b>{fmt(metrics?.avg_diagnosis_latency_ms, "ms")}</b>
        </div>
        <div className="metric">
          Avg MTTR <b>{fmt(metrics?.avg_mttr_s, "s")}</b>
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<AlertDashboard />} />
          <Route path="/alerts/:id" element={<InvestigationView />} />
          <Route path="/alerts/:id/diagnosis" element={<DiagnosisPanel />} />
          <Route path="/alerts/:id/remediation" element={<RemediationPanel />} />
          <Route path="/alerts/:id/approval" element={<ApprovalScreen />} />
        </Routes>
      </main>
    </div>
  );
}
