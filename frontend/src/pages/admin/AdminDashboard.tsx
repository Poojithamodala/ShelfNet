import { useEffect, useState } from "react";
import api from "../../api/axios";
import "../../styles/dashboard.css";
import "../../styles/common.css";

import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Legend
} from "recharts";

type AdminKpis = {
  total_warehouses: number;
  active_batches: number;
  inactive_batches: number;
  total_batches: number;
  total_sensors: number;
  active_alerts: number;
  critical_batches: number;
};

type AlertAnalytics = { alert_type: string; count: number };
type WarehouseSummary = {
  warehouse_id: string;
  active_batches: number;
  inactive_batches: number;
  active_alerts: number;
};
type FruitOverview = {
  fruit: string;
  avg_remaining_shelf_life: number;
};
type SensorHealth = {
  online_sensors: number;
  offline_sensors: number;
};
type UserSummary = { role: string; count: number };

const COLORS = ["#4CAF50", "#FF9800", "#F44336", "#2196F3", "#9C27B0"];

export default function AdminDashboard() {
  const [kpis, setKpis] = useState<AdminKpis | null>(null);
  const [alerts, setAlerts] = useState<AlertAnalytics[]>([]);
  const [warehouses, setWarehouses] = useState<WarehouseSummary[]>([]);
  const [fruits, setFruits] = useState<FruitOverview[]>([]);
  const [sensorHealth, setSensorHealth] = useState<SensorHealth | null>(null);
  const [users, setUsers] = useState<UserSummary[]>([]);

  useEffect(() => {
    const load = async () => {
      const [k, a, w, f, s, u] = await Promise.all([
        api.get("/admin/kpis"),
        api.get("/admin/alerts/analytics"),
        api.get("/admin/warehouses/summary"),
        api.get("/admin/fruits/overview"),
        api.get("/admin/sensors/health"),
        api.get("/admin/users/summary")
      ]);

      setKpis(k.data);
      setAlerts(a.data);
      setWarehouses(w.data);
      setFruits(f.data);
      setSensorHealth(s.data);
      setUsers(u.data);
    };

    load();
  }, []);

  if (!kpis) return <p>Loading...</p>;

  const sensorData = sensorHealth
    ? [
        { name: "Online", value: sensorHealth.online_sensors },
        { name: "Offline", value: sensorHealth.offline_sensors }
      ]
    : [];

  return (
    <div className="page">
      {/* HEADER */}
      <div className="page-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p>System Overview</p>
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="dashboard-grid">
        <Card title="Warehouses" value={kpis.total_warehouses} />
        <Card title="Active Batches" value={kpis.active_batches} />
        <Card title="Inactive Batches" value={kpis.inactive_batches} />
        <Card title="Total Batches" value={kpis.total_batches} />
        <Card title="Sensors" value={kpis.total_sensors} />
        <Card title="Active Alerts" value={kpis.active_alerts} />
        <Card title="Critical Batches" value={kpis.critical_batches} />
      </div>

      <h2 style={{ marginTop: "24px" }}>System Analytics</h2>

      {/* CHARTS */}
      <div className="charts">

        {/* Alert Distribution */}
        <ChartCard title="Alert Distribution">
          <PieChart>
            <Pie data={alerts} dataKey="count" nameKey="alert_type" outerRadius={80}>
              {alerts.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [value, name]} />
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
          </PieChart>
        </ChartCard>

        {/* Sensor Health */}
        <ChartCard title="Sensor Health">
          <PieChart>
            <Pie data={sensorData} dataKey="value" nameKey="name" outerRadius={80}>
              {sensorData.map((_, i) => (
                <Cell key={i} fill={COLORS[i]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [value, name]} />
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
          </PieChart>
        </ChartCard>

        {/* ✅ Active + Inactive Batches per Warehouse - Touching grouped bars */}
        <ChartCard title="Batches per Warehouse">
          <BarChart
            data={warehouses}
            barCategoryGap="40%"
            barGap={0}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="warehouse_id" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
            <Bar dataKey="active_batches" name="Active Batches" fill="#4CAF50" maxBarSize={50} radius={[0, 0, 0, 0]} />
            <Bar dataKey="inactive_batches" name="Inactive Batches" fill="#FF9800" maxBarSize={50} radius={[0, 0, 0, 0]} />
          </BarChart>
        </ChartCard>

        {/* Alerts per Warehouse */}
        <ChartCard title="Alerts per Warehouse">
          <BarChart data={warehouses} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="warehouse_id" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend
              formatter={() => (
                <span style={{ fontSize: "12px", color: "#374151" }}>Active Alerts</span>
              )}
            />
            <Bar dataKey="active_alerts" fill="#F44336" name="Active Alerts" maxBarSize={40} />
          </BarChart>
        </ChartCard>

        {/* Average Shelf Life by Fruit */}
        <ChartCard title="Average Shelf Life by Fruit">
          <BarChart data={fruits} barCategoryGap="30%">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="fruit" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend
              formatter={() => (
                <span style={{ fontSize: "12px", color: "#374151" }}>Avg Shelf Life (days)</span>
              )}
            />
            <Bar dataKey="avg_remaining_shelf_life" fill="#2196F3" name="Avg Shelf Life (days)" maxBarSize={40} />
          </BarChart>
        </ChartCard>

        {/* User Roles */}
        <ChartCard title="User Roles">
          <PieChart>
            <Pie data={users} dataKey="count" nameKey="role" outerRadius={80}>
              {users.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip formatter={(value, name) => [value, name]} />
            <Legend
              layout="vertical"
              align="right"
              verticalAlign="middle"
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
          </PieChart>
        </ChartCard>

      </div>
    </div>
  );
}

/* KPI CARD */
function Card({ title, value }: { title: string; value: number }) {
  return (
    <div className="dashboard-card">
      <h3>{title}</h3>
      <p>{value}</p>
    </div>
  );
}

/* CHART CARD */
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