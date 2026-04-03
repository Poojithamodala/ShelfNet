import { useEffect, useState } from "react";
import { getUser } from "../../utils/auth";
import { getManagerAlerts, resolveManagerAlert } from "../../api/manager.api";
import { getWarehouseById } from "../../api/warehouse.api";
import "../../styles/manager.css";
import "../../styles/common.css";

type AlertItem = {
  alert_id?: string;
  _id?: string;
  created_at: string;
  batch_id: string;
  alert_type: string;
  severity?: string;
  message?: string;
  description?: string;
  occurrences?: number;
  last_seen_at?: string;
  resolved?: boolean;
};

type Warehouse = {
  warehouse_id?: string;
  name?: string;
};

export default function ManagerAlerts() {
  const user        = getUser();
  const warehouseId = user?.warehouse_id;

  const [alerts, setAlerts]                   = useState<AlertItem[]>([]);
  const [warehouse, setWarehouse]             = useState<Warehouse | null>(null);
  const [loading, setLoading]                 = useState(true);
  const [error, setError]                     = useState<string | null>(null);
  const [typeFilter, setTypeFilter]           = useState("ALL");
  const [severityFilter, setSeverityFilter]   = useState("ALL");
  const [statusFilter, setStatusFilter]       = useState("ALL");

  useEffect(() => {
    const fetchAlerts = async () => {
      if (!warehouseId) {
        setError("No warehouse assigned to this manager.");
        setLoading(false);
        return;
      }

      setLoading(true);

      try {
        const [alertRes, warehouseRes] = await Promise.all([
          getManagerAlerts(warehouseId),
          getWarehouseById(warehouseId)
        ]);
        setAlerts(alertRes.data);
        setWarehouse(warehouseRes.data);
        setError(null);
      } catch (err: unknown) {
        type AxiosError = { response?: { data?: { detail?: string } } };
        const message =
          (err as AxiosError)?.response?.data?.detail || "Could not load alerts";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    if (warehouseId) {
      void fetchAlerts();
    } else {
      setLoading(false);
    }
  }, [warehouseId]);

  const onResolve = async (alert_id: string) => {
    try {
      await resolveManagerAlert(alert_id);
      const [alertRes, warehouseRes] = await Promise.all([
        getManagerAlerts(warehouseId!),
        getWarehouseById(warehouseId!)
      ]);
      setAlerts(alertRes.data);
      setWarehouse(warehouseRes.data);
    } catch (err: unknown) {
      type AxiosError = { response?: { data?: { detail?: string } } };
      const message =
        (err as AxiosError)?.response?.data?.detail || "Could not resolve alert";
      setError(message);
    }
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  void onResolve;

  const filteredAlerts = alerts.filter((a) => {
    if (typeFilter     !== "ALL" && a.alert_type       !== typeFilter)     return false;
    if (severityFilter !== "ALL" && (a.severity ?? "LOW") !== severityFilter) return false;
    if (statusFilter === "ACTIVE"   &&  a.resolved) return false;
    if (statusFilter === "RESOLVED" && !a.resolved) return false;
    return true;
  });

  if (loading) return <p>Loading alerts...</p>;
  if (error)   return <p>{error}</p>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Warehouse Alerts</h1>
          <p>{warehouse?.name || `Warehouse ${warehouseId}`} ({warehouseId})</p>
        </div>
      </div>

      <div className="filters">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
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

        <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
          <option value="ALL">All Severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="HIGH">High</option>
          <option value="LOW">Low</option>
        </select>

        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="ALL">All Status</option>
          <option value="ACTIVE">Active</option>
          <option value="RESOLVED">Resolved</option>
        </select>
      </div>

      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Batch</th>
            <th>Type</th>
            <th>Severity</th>
            <th>Message</th>
            <th>Count</th>
            <th>Last Seen</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {filteredAlerts.length === 0 ? (
            <tr>
              <td colSpan={7} className="empty">No current alerts</td>
            </tr>
          ) : (
            filteredAlerts.map((alert) => (
              <tr key={alert.alert_id || alert._id}>
                <td>{alert.batch_id}</td>
                <td>
                  <span className={`alert-tag ${alert.alert_type}`}>
                    {alert.alert_type.replace(/_/g, " ")}
                  </span>
                </td>
                <td>
                  <span className={`severity-tag ${alert.severity ?? "LOW"}`}>
                    {alert.severity ?? "LOW"}
                  </span>
                </td>
                <td>{alert.message || alert.description || "No details"}</td>
                <td>{alert.occurrences || 1}</td>
                <td>
                  {alert.last_seen_at
                    ? new Date(alert.last_seen_at).toLocaleString()
                    : new Date(alert.created_at).toLocaleString()}
                </td>
                <td>
                  <span className={alert.resolved ? "status resolved" : "status active"}>
                    {alert.resolved ? "RESOLVED" : "ACTIVE"}
                  </span>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}