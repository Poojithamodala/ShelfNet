import { useEffect, useState } from "react";
import { getUser } from "../../utils/auth";
import { getManagerKpis } from "../../api/manager.api";
import { getWarehouseById } from "../../api/warehouse.api";
import api from "../../api/axios";
import "../../styles/manager.css";
import "../../styles/common.css";

import {
  PieChart, Pie, Cell, Tooltip,
  BarChart, Bar, XAxis, YAxis,
  CartesianGrid, ResponsiveContainer, Legend,
} from "recharts";

type ManagerKpis = {
  active_batches:   number;
  selled_batches:   number;
  total_batches:    number;
  active_alerts:    number;
  critical_alerts:  number;
  resolved_alerts:  number;
  expiring_batches: number;
  sensors_online:   number;
  sensors_total:    number;
};

type Warehouse       = { warehouse_id?: string; name?: string };
type BatchStatusItem = { label: string; count: number };
type AlertItem       = { alert_type: string; active: number; resolved: number };
type FruitShelfLife  = { fruit: string; avg_remaining_shelf_life: number; total_batches: number };
type SensorHealth    = { name: string; value: number };
type ExpiryBucket    = { label: string; count: number };

const COLORS = ["#4CAF50", "#FF9800", "#F44336", "#2196F3", "#9C27B0"];

export default function ManagerDashboard() {
  const user        = getUser();
  const warehouseId = user?.warehouse_id;

  const [kpis,         setKpis]         = useState<ManagerKpis | null>(null);
  const [warehouse,    setWarehouse]    = useState<Warehouse | null>(null);
  const [batchStatus,  setBatchStatus]  = useState<BatchStatusItem[]>([]);
  const [alerts,       setAlerts]       = useState<AlertItem[]>([]);
  const [fruitShelf,   setFruitShelf]   = useState<FruitShelfLife[]>([]);
  const [sensorHealth, setSensorHealth] = useState<SensorHealth[]>([]);
  const [expiry,       setExpiry]       = useState<ExpiryBucket[]>([]);
  const [error,        setError]        = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!warehouseId) {
        setError("No warehouse assigned to this manager.");
        return;
      }

      try {
        const [kpiRes, warehouseRes, statusRes, alertRes, fruitRes, sensorRes, expiryRes] =
          await Promise.all([
            getManagerKpis(warehouseId),
            getWarehouseById(warehouseId),
            api.get(`/manager/${warehouseId}/analytics/batch-status`),
            api.get(`/manager/${warehouseId}/analytics/alerts`),
            api.get(`/manager/${warehouseId}/analytics/fruit-shelf-life`),
            api.get(`/manager/${warehouseId}/analytics/sensor-health`),
            api.get(`/manager/${warehouseId}/analytics/expiry-distribution`),
          ]);

        setKpis(kpiRes.data);
        setWarehouse(warehouseRes.data);
        setBatchStatus(statusRes.data);
        setAlerts(alertRes.data);
        setFruitShelf(fruitRes.data);
        setSensorHealth(sensorRes.data);
        setExpiry(expiryRes.data);
        setError(null);
      } catch (err: unknown) {
        type AxiosError = { response?: { data?: { detail?: string } } };
        const message =
          (err as AxiosError)?.response?.data?.detail || "Failed to load dashboard";
        setError(message);
      }
    };

    load();
  }, [warehouseId]);

  if (error)  return <p>{error}</p>;
  if (!kpis)  return <p>Loading KPI summary...</p>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Manager Dashboard</h1>
          <p>{warehouse?.name} ({warehouseId})</p>
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="dashboard-grid">
        <Card title="Active Batches"     value={kpis.active_batches} />
        <Card title="Sold Batches"       value={kpis.selled_batches} />
        <Card title="Total Batches"      value={kpis.total_batches} />
        <Card title="Active Alerts"      value={kpis.active_alerts}    color="#F44336" />
        <Card title="Critical Alerts"    value={kpis.critical_alerts}  color="#FF9800" />
        <Card title="Resolved Alerts"    value={kpis.resolved_alerts}  color="#4CAF50" />
        <Card title="Expiring (≤5 days)" value={kpis.expiring_batches} color="#FF9800" />
        <Card title="Sensors Online"     value={kpis.sensors_online} />
        <Card title="Total Sensors"      value={kpis.sensors_total} />
      </div>

      <h2 style={{ marginTop: "24px" }}>Warehouse Analytics</h2>

      <div className="charts">

        {/* Sensor Health — Pie */}
        <ChartCard title="Sensor Health">
          <PieChart>
            <Pie data={sensorHealth} dataKey="value" nameKey="name" outerRadius={80}>
              {sensorHealth.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [value, name]} />
            <Legend
              layout="vertical" align="right" verticalAlign="middle"
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
          </PieChart>
        </ChartCard>

        {/* Batch Status — Pie */}
        <ChartCard title="Batch Status Breakdown">
          <PieChart>
            <Pie data={batchStatus} dataKey="count" nameKey="label" outerRadius={80}>
              {batchStatus.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [value, name]} />
            <Legend
              layout="vertical" align="right" verticalAlign="middle"
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
          </PieChart>
        </ChartCard>

        {/* Alert Type Breakdown — Active + Resolved grouped bars */}
        <ChartCard title="Alert Type Breakdown">
          <BarChart data={alerts} barCategoryGap="40%" barGap={0}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="alert_type" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
            <Bar dataKey="active"   name="Active Alerts"   fill="#F44336" maxBarSize={50} radius={[4, 4, 0, 0]} />
            <Bar dataKey="resolved" name="Resolved Alerts" fill="#4CAF50" maxBarSize={50} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ChartCard>

        {/* Avg Shelf Life by Fruit — Bar */}
        <ChartCard title="Avg Shelf Life by Fruit">
          <BarChart data={fruitShelf} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="fruit" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend
              formatter={() => (
                <span style={{ fontSize: "12px", color: "#374151" }}>Avg Shelf Life (days)</span>
              )}
            />
            <Bar
              dataKey="avg_remaining_shelf_life"
              name="Avg Shelf Life (days)"
              fill="#2196F3"
              maxBarSize={40}
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        </ChartCard>

        {/* Expiry Distribution — Bar */}
        <ChartCard title="Batch Expiry Distribution">
          <BarChart data={expiry} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="label" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend
              formatter={() => (
                <span style={{ fontSize: "12px", color: "#374151" }}>Batches</span>
              )}
            />
            <Bar dataKey="count" name="Batches" maxBarSize={40} radius={[4, 4, 0, 0]}>
              {expiry.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ChartCard>

      </div>
    </div>
  );
}

function Card({ title, value, color }: { title: string; value: number; color?: string }) {
  return (
    <div className="dashboard-card">
      <h3>{title}</h3>
      <p style={color ? { color } : undefined}>{value}</p>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactElement }) {
  return (
    <div className="dashboard-card" style={{ height: "420px" }}>
      <h3>{title}</h3>
      <div style={{ width: "100%", height: "350px" }}>
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}