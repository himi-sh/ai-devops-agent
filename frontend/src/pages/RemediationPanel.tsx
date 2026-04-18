import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Remediation } from "../api";
import AlertNav from "../components/AlertNav";

function DiffView({ diff }: { diff: string }) {
  return (
    <pre>
      {diff.split("\n").map((line, i) => {
        let cls = "";
        if (line.startsWith("+") && !line.startsWith("+++")) cls = "diff-add";
        else if (line.startsWith("-") && !line.startsWith("---")) cls = "diff-del";
        else if (line.startsWith("@@") || line.startsWith("---") || line.startsWith("+++")) cls = "diff-meta";
        return (
          <div key={i} className={cls}>
            {line || " "}
          </div>
        );
      })}
    </pre>
  );
}

export default function RemediationPanel() {
  const { id } = useParams();
  const nav = useNavigate();
  const [rem, setRem] = useState<Remediation | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getRemediation(Number(id)).then(setRem);
  }, [id]);

  const run = async () => {
    if (!id) return;
    setLoading(true);
    setErr(null);
    try {
      setRem(await api.remediate(Number(id)));
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h2>Alert #{id} — Remediation</h2>
      <AlertNav id={id!} />

      <div className="panel">
        <h3>Suggested patch</h3>
        {!rem && !loading && (
          <button onClick={run}>Generate remediation</button>
        )}
        {loading && <div>Generating fix with LLM…</div>}
        {err && <div style={{ color: "#ef4444" }}>Error: {err}</div>}
        {rem && (
          <>
            <div>Target: <code>{rem.target_file}</code></div>
            <div>Status: <span className={`badge status-${rem.status === "applied" ? "resolved" : "diagnosed"}`}>{rem.status}</span></div>
            <h4>Rationale</h4>
            <p>{rem.rationale}</p>
            <h4>Unified diff</h4>
            {rem.diff ? <DiffView diff={rem.diff} /> : <em>No diff produced</em>}
          </>
        )}
      </div>

      {rem && rem.status === "pending" && (
        <button onClick={() => nav(`/alerts/${id}/approval`)}>
          Send for approval →
        </button>
      )}
    </>
  );
}
