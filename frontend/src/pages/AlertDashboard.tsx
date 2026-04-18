import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, Alert } from "../api";

export default function AlertDashboard() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const nav = useNavigate();

  useEffect(() => {
    const load = () => api.listAlerts().then(setAlerts).catch(() => {});
    load();
    const id = setInterval(load, 2000);
    return () => clearInterval(id);
  }, []);

  return (
    <>
      <h2>Alert Dashboard</h2>
      {alerts.length === 0 ? (
        <div className="empty">
          No alerts yet. Trigger the scenario:
          <pre style={{ marginTop: 12 }}>python -m backend.scenarios.code_exception</pre>
        </div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Service</th>
              <th>Exception</th>
              <th>Severity</th>
              <th>Status</th>
              <th>Events</th>
              <th>Last seen</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr
                key={a.id}
                className="clickable"
                onClick={() => nav(`/alerts/${a.id}`)}
              >
                <td>{a.id}</td>
                <td>{a.service}</td>
                <td>{a.exception_type}</td>
                <td>
                  <span className={`badge sev-${a.severity}`}>{a.severity}</span>
                </td>
                <td>
                  <span className={`badge status-${a.status}`}>{a.status}</span>
                </td>
                <td>{a.event_count}</td>
                <td>{new Date(a.last_seen).toLocaleTimeString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
