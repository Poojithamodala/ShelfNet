import { useEffect, useState } from "react";
import { getSalesExpiryReport } from "../../api/sales.api";
import { getUser } from "../../utils/auth";
import "../../styles/sales.css";
import "../../styles/common.css";

type SalesReport = {
  batch_id: string;
  fruit: string;
  warehouse_id: string;
  expected_expiry_date: string;
  remaining_shelf_life_days: number;
};

export default function SalesReports() {
  const user = getUser();
  const warehouseId = user?.warehouse_id;

  const [reports, setReports] = useState<SalesReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!warehouseId) {
      setError("No warehouse assigned to this user.");
      setLoading(false);
      return;
    }
    const load = async () => {
      try {
        const res = await getSalesExpiryReport();
        setReports(res.data);
        setError(null);
      } catch (err) {
        setError((err as any)?.response?.data?.detail || "Failed to load expiry reports");
      } finally {
        setLoading(false);
      }
    };
    void load();
  }, [warehouseId]);

  if (loading) return <p>Loading expiry report...</p>;
  if (error) return <p>{error}</p>;

  const warehouseText = warehouseId ? `Warehouse ${warehouseId}` : "All Warehouses";

  return (
    <div className="sales-page">
      <div className="sales-header">
        <div>
          <h1>Expiry Forecast</h1>
          <p className="sales-warehouse">{warehouseText}</p>
        </div>
      </div>

      <div className="table-wrapper">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>Batch</th>
              <th>Fruit</th>
              <th>Warehouse</th>
              <th>Expiry Date</th>
              <th>Remaining Days</th>
            </tr>
          </thead>
          <tbody>
            {reports.length === 0 ? (
              <tr>
                <td colSpan={5} className="empty">
                  No expiry forecast data available.
                </td>
              </tr>
            ) : (
              reports.map((row) => (
                <tr key={`${row.batch_id}-${row.expected_expiry_date}`}>
                  <td>{row.batch_id}</td>
                  <td>{row.fruit}</td>
                  <td>{row.warehouse_id}</td>
                  <td>{row.expected_expiry_date}</td>
                  <td>{row.remaining_shelf_life_days}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}