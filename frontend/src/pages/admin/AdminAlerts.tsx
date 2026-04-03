import { useEffect, useState } from "react";
import api from "../../api/axios";
import "../../styles/alerts.css";
import "../../styles/common.css";

type Alert = {
  batch_id: string;
  warehouse_id: string;
  alert_type: string;
  severity: string;
  message: string;
  occurrences: number;
  last_seen_at: string;
  resolved: boolean;
};

export default function AdminAlerts() {
  const [alerts, setAlerts]                     = useState<Alert[]>([]);
  const [typeFilter, setTypeFilter]             = useState("ALL");
  const [severityFilter, setSeverityFilter]     = useState("ALL");
  const [statusFilter, setStatusFilter]         = useState("ALL");

  useEffect(() => {
    api.get("/alerts").then((res) => setAlerts(res.data));
  }, []);

  const filteredAlerts = alerts.filter((a) => {
    const severity = a.severity ?? "HIGH";
    if (typeFilter     !== "ALL" && a.alert_type !== typeFilter)   return false;
    if (severityFilter !== "ALL" && severity     !== severityFilter) return false;
    if (statusFilter === "ACTIVE"   &&  a.resolved) return false;
    if (statusFilter === "RESOLVED" && !a.resolved) return false;
    return true;
  });

  return (
    <div className="alerts-page">
      <h2>System Alerts</h2>
      <p className="subtitle">Real-time monitoring across all warehouses</p>

      <div className="filters">
        <select onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="ALL">All Types</option>
          <option value="SPOILED">Spoiled</option>
          <option value="CRITICAL">Critical</option>
          <option value="WARNING">Warning</option>
          <option value="TEMP_HIGH">Temp High</option>
          <option value="TEMP_LOW">Temp Low</option>
          <option value="HUMIDITY_HIGH">Humidity High</option>
          <option value="HUMIDITY_LOW">Humidity Low</option>
          <option value="ETHYLENE_HIGH">Ethylene High</option>
          <option value="CO2_HIGH">CO₂ High</option>
          <option value="O2_LOW">O₂ Low</option>
          <option value="POWER_FAILURE">Power Failure</option>
          <option value="INFO">Info</option>
        </select>

        <select onChange={(e) => setSeverityFilter(e.target.value)}>
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="LOW">Low</option>
        </select>

        <select onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Batch</th>
            <th>Warehouse</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Count</th>
            <th>Last Seen</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {filteredAlerts.map((a, i) => (
            <tr key={i}>
              <td>{a.batch_id}</td>
              <td>{a.warehouse_id}</td>
              <td>
                <span className={`alert-tag ${a.alert_type}`}>
                  {a.alert_type.replace(/_/g, " ")}
                </span>
              </td>
              <td>
                <span className={`severity-tag ${a.severity ?? "HIGH"}`}>
                  {a.severity ?? "HIGH"}
                </span>
              </td>
              <td>{a.message}</td>
              <td>{a.occurrences}</td>
              <td>{new Date(a.last_seen_at).toLocaleString()}</td>
              <td>
                <span className={a.resolved ? "status resolved" : "status active"}>
                  {a.resolved ? "RESOLVED" : "ACTIVE"}
                </span>
              </td>
            </tr>
          ))}
          {filteredAlerts.length === 0 && (
            <tr>
              <td colSpan={8} className="empty">No current alerts</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}