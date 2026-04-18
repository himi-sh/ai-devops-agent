import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Remediation } from "../api";
import AlertNav from "../components/AlertNav";

export default function ApprovalScreen() {
  const { id } = useParams();
  const nav = useNavigate();
  const [rem, setRem] = useState<Remediation | null>(null);
  const [working, setWorking] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getRemediation(Number(id)).then(setRem);
  }, [id]);

  const approve = async () => {
    if (!rem) return;
    setWorking(true);
    setErr(null);
    try {
      setRem(await api.approve(rem.id));
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setWorking(false);
    }
  };

  const reject = async () => {
    if (!rem) return;
    setWorking(true);
    try {
      setRem(await api.reject(rem.id));
    } finally {
      setWorking(false);
    }
  };

  if (!rem) {
    return (
      <>
        <h2>Alert #{id} — Approval</h2>
        <AlertNav id={id!} />
        <div className="panel">No remediation generated yet.</div>
      </>
    );
  }

  return (
    <>
      <h2>Alert #{id} — Approval / Execution</h2>
      <AlertNav id={id!} />

      <div className="panel">
        <h3>Review & execute</h3>
        <div>File to patch: <code>{rem.target_file}</code></div>
        <div>Current status: <span className={`badge status-${rem.status === "applied" ? "resolved" : "diagnosed"}`}>{rem.status}</span></div>
        <h4>Rationale</h4>
        <p>{rem.rationale}</p>
        <h4>Diff</h4>
        <pre>{rem.diff}</pre>
        {err && <div style={{ color: "#ef4444" }}>Error: {err}</div>}

        {rem.status === "pending" && (
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button disabled={working} onClick={approve}>
              Approve & apply
            </button>
            <button disabled={working} className="danger" onClick={reject}>
              Reject
            </button>
          </div>
        )}
        {rem.status === "applied" && (
          <>
            <p style={{ color: "#10b981", marginTop: 12 }}>
              ✓ Patch applied to <code>{rem.target_file}</code>.
              Re-run the scenario — the bug should no longer recur.
            </p>
            <button className="secondary" onClick={() => nav("/")}>
              Back to dashboard
            </button>
          </>
        )}
        {rem.status === "rejected" && (
          <p style={{ color: "#ef4444", marginTop: 12 }}>Rejected.</p>
        )}
      </div>
    </>
  );
}
