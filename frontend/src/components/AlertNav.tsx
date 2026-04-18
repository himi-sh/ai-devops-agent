import { NavLink } from "react-router-dom";

export default function AlertNav({ id }: { id: string | number }) {
  const link = (to: string, label: string) => (
    <NavLink
      to={to}
      end
      className={({ isActive }) => (isActive ? "active" : "")}
    >
      {label}
    </NavLink>
  );
  return (
    <div className="nav">
      {link(`/alerts/${id}`, "Investigation")}
      {link(`/alerts/${id}/diagnosis`, "Diagnosis")}
      {link(`/alerts/${id}/remediation`, "Remediation")}
      {link(`/alerts/${id}/approval`, "Approval")}
    </div>
  );
}
