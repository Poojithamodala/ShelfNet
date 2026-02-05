import { useEffect, useState } from "react";
import api from "../../api/axios";
import "../../styles/alerts.css";

type Alert = {
  batch_id: string;
  warehouse_id: string;
  alert_type: string;
  message: string;
  occurrences: number;
  last_seen_at: string;
  resolved: boolean;
};

export default function AdminAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [typeFilter, setTypeFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    const res = await api.get("/alerts");
    setAlerts(res.data);
  };

  const filteredAlerts = alerts.filter((a) => {
    if (typeFilter !== "ALL" && a.alert_type !== typeFilter) return false;
    if (statusFilter === "ACTIVE" && a.resolved) return false;
    if (statusFilter === "RESOLVED" && !a.resolved) return false;
    return true;
  });

  return (
    <div className="alerts-page">
      <h2>System Alerts</h2>
      <p className="subtitle">
        Real-time monitoring across all warehouses
      </p>

      {/* Filters */}
      <div className="filters">
        <select onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="ALL">All Types</option>
          <option value="CRITICAL">Critical</option>
          <option value="WARNING">Warning</option>
          <option value="INFO">Info</option>
          <option value="SPOILED">Spoiled</option>
        </select>

        <select onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      {/* Table */}
      <table className="alerts-table">
        <thead>
          <tr>
            <th>Batch</th>
            <th>Warehouse</th>
            <th>Type</th>
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
                  {a.alert_type}
                </span>
              </td>
              <td>{a.message}</td>
              <td>{a.occurrences}</td>
              <td>
                {new Date(a.last_seen_at).toLocaleString()}
              </td>
              <td>
                <span
                  className={
                    a.resolved ? "status resolved" : "status active"
                  }
                >
                  {a.resolved ? "RESOLVED" : "ACTIVE"}
                </span>
              </td>
            </tr>
          ))}

          {filteredAlerts.length === 0 && (
            <tr>
              <td colSpan={7} className="empty">
                No alerts found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
