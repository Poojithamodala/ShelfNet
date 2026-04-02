import { useEffect, useState } from "react";
import { getSalesKpis } from "../../api/sales.api";
import api from "../../api/axios";
import { getUser } from "../../utils/auth";
import "../../styles/sales.css";
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
  Legend,
} from "recharts";
 
type SalesKpis = {
  sellable_batches: number;
  sell_soon_batches: number;
  not_sellable_batches: number;
  sold_batches: number;
  total_batches: number;
  active_batches: number;
};
 
type SellabilityItem = { category: string; count: number };
type FruitShelfLife  = { fruit: string; avg_remaining_shelf_life: number; total_batches: number };
type BatchStatusItem = { label: string; count: number };
type ExpiryBucket    = { label: string; count: number };
 
const COLORS = ["#4CAF50", "#FF9800", "#F44336", "#2196F3", "#9C27B0"];
 
export default function SalesDashboard() {
  const user = getUser();
  const warehouseId = user?.warehouse_id;
 
  const [kpis, setKpis]               = useState<SalesKpis | null>(null);
  const [sellability, setSellability] = useState<SellabilityItem[]>([]);
  const [fruitShelf, setFruitShelf]   = useState<FruitShelfLife[]>([]);
  const [batchStatus, setBatchStatus] = useState<BatchStatusItem[]>([]);
  const [expiry, setExpiry]           = useState<ExpiryBucket[]>([]);
 
  useEffect(() => {
    if (!warehouseId) return;
 
    const load = async () => {
      try {
        const [kpiRes, sellRes, fruitRes, statusRes, expiryRes] = await Promise.all([
          getSalesKpis(),
          api.get("/sales/analytics/sellability"),
          api.get("/sales/analytics/fruit-shelf-life"),
          api.get("/sales/analytics/batch-status"),
          api.get("/sales/analytics/expiry-distribution"),
        ]);
 
        setKpis(kpiRes.data);
        setSellability(sellRes.data);
        setFruitShelf(fruitRes.data);
        setBatchStatus(statusRes.data);
        setExpiry(expiryRes.data);
      } catch (err) {
        console.error("Failed to load sales dashboard", err);
      }
    };
 
    void load();
  }, [warehouseId]);
 
  if (!kpis) return <p>Loading sales KPIs...</p>;
 
  const warehouseText = warehouseId ? `Warehouse ${warehouseId}` : "All Warehouses";
 
  return (
    <div className="page">
      {/* HEADER */}
      <div className="page-header">
        <div>
          <h1>Sales Dashboard</h1>
          <p className="sales-warehouse">{warehouseText}</p>
        </div>
      </div>
 
      {/* KPI CARDS */}
      <div className="dashboard-grid">
        <Card title="Sell Now"       value={kpis.sellable_batches} />
        <Card title="Sell Soon"      value={kpis.sell_soon_batches} />
        <Card title="Do Not Sell"    value={kpis.not_sellable_batches} />
        <Card title="Active Batches" value={kpis.active_batches} />
        <Card title="Batches Sold"   value={kpis.sold_batches} />
        <Card title="Total Batches"  value={kpis.total_batches} />
      </div>
 
      <h2 style={{ marginTop: "24px" }}>Sales Analytics</h2>
 
      {/* CHARTS */}
      <div className="charts">
 
        {/* Sellability Distribution — Pie */}
        <ChartCard title="Sellability Distribution">
          <PieChart>
            <Pie data={sellability} dataKey="count" nameKey="category" outerRadius={80}>
              {sellability.map((_, i) => (
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
              layout="vertical"
              align="right"
              verticalAlign="middle"
              formatter={(value) => (
                <span style={{ fontSize: "12px", color: "#374151" }}>{value}</span>
              )}
            />
          </PieChart>
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
 
function Card({ title, value }: { title: string; value: number }) {
  return (
    <div className="dashboard-card">
      <h3>{title}</h3>
      <p>{value}</p>
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