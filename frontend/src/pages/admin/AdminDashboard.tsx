import { useEffect, useState } from "react";
import api from "../../api/axios";

export default function AdminDashboard() {
  const [kpis, setKpis] = useState<any>(null);

  useEffect(() => {
    api.get("/admin/kpis").then(res => setKpis(res.data));
  }, []);

  if (!kpis) return <p>Loading...</p>;

  return (
    <>
      <h1>Admin Dashboard</h1>

      <div className="grid">
        <Card title="Warehouses" value={kpis.total_warehouses} />
        <Card title="Active Batches" value={kpis.active_batches} />
        <Card title="Sensors" value={kpis.total_sensors} />
        <Card title="Active Alerts" value={kpis.active_alerts} />
        <Card title="Critical Batches" value={kpis.critical_batches} />
      </div>
    </>
  );
}

function Card({ title, value }: any) {
  return (
    <div className="card">
      <h3>{title}</h3>
      <p>{value}</p>
    </div>
  );
}
