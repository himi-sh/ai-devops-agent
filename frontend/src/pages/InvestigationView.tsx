import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api, Alert } from "../api";
import AlertNav from "../components/AlertNav";

export default function InvestigationView() {
  const { id } = useParams();
  const nav = useNavigate();
  const [alert, setAlert] = useState<Alert | null>(null);

  useEffect(() => {
    if (!id) return;
    api.getAlert(Number(id)).then(setAlert);
  }, [id]);

  if (!alert) return <div>Loading…</div>;

  const top = alert.events?.[0];

  return (
    <>
      <h2>Alert #{alert.id} — Investigation</h2>
      <AlertNav id={alert.id} />

      <div className="panel">
        <h3>Summary</h3>
        <div>Service: <b>{alert.service}</b></div>
        <div>Signature: <code>{alert.signature}</code></div>
        <div>
          Severity: <span className={`badge sev-${alert.severity}`}>{alert.severity}</span>
          {" "}
          Status: <span className={`badge status-${alert.status}`}>{alert.status}</span>
        </div>
        <div>Events observed: {alert.event_count}</div>
        <div>First seen: {new Date(alert.first_seen).toLocaleString()}</div>
        <div>Last seen: {new Date(alert.last_seen).toLocaleString()}</div>
      </div>

      {top && (
        <div className="panel">
          <h3>Latest exception</h3>
          <div><b>{alert.exception_type}:</b> {top.message}</div>
          <pre style={{ marginTop: 8 }}>{top.stack_trace}</pre>
        </div>
      )}

      <div className="panel">
        <h3>Event timeline</h3>
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Time</th>
              <th>Message</th>
            </tr>
          </thead>
          <tbody>
            {(alert.events ?? []).map((e) => (
              <tr key={e.id}>
                <td>{e.id}</td>
                <td>{new Date(e.created_at).toLocaleTimeString()}</td>
                <td>{e.message}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <button onClick={() => nav(`/alerts/${alert.id}/diagnosis`)}>
        Go to Diagnosis →
      </button>
    </>
  );
}
