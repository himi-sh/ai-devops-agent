import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Diagnosis } from "../api";
import AlertNav from "../components/AlertNav";

export default function DiagnosisPanel() {
  const { id } = useParams();
  const nav = useNavigate();
  const [diag, setDiag] = useState<Diagnosis | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getDiagnosis(Number(id)).then(setDiag);
  }, [id]);

  const run = async () => {
    if (!id) return;
    setLoading(true);
    setErr(null);
    try {
      setDiag(await api.diagnose(Number(id)));
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h2>Alert #{id} — Diagnosis</h2>
      <AlertNav id={id!} />

      <div className="panel">
        <h3>Root cause (LLM)</h3>
        {!diag && !loading && (
          <button onClick={run}>Run LLM diagnosis</button>
        )}
        {loading && <div>Asking the model…</div>}
        {err && <div style={{ color: "#ef4444" }}>Error: {err}</div>}
        {diag && (
          <>
            <p style={{ fontSize: 15, lineHeight: 1.6 }}>{diag.root_cause}</p>
            <div>
              Confidence: <b>{Math.round(diag.confidence * 100)}%</b>
              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{ width: `${Math.round(diag.confidence * 100)}%` }}
                />
              </div>
            </div>
            {diag.contributing_factors.length > 0 && (
              <>
                <h4>Contributing factors</h4>
                <ul>
                  {diag.contributing_factors.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </>
            )}
            <div style={{ fontSize: 12, opacity: 0.6 }}>
              LLM latency: {diag.latency_ms} ms
            </div>
          </>
        )}
      </div>

      {diag && (
        <button onClick={() => nav(`/alerts/${id}/remediation`)}>
          Generate fix →
        </button>
      )}
    </>
  );
}
