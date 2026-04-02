import { useEffect, useState } from "react";
import { getUser } from "../../utils/auth";
import { getSalesBatches, closeSalesBatch } from "../../api/sales.api";
import "../../styles/manager.css";
import "../../styles/common.css";

type SalesBatch = {
  batch_id: string;
  fruit?: string;
  quantity_kg?: number;
  warehouse_id?: string;
  predicted_remaining_shelf_life_days?: number | null;
  remaining_shelf_life_days?: number | null;
  sales_category?: string;
  status?: string;
};

const getWarehouseIdFromToken = (): string | null => {
  const user = getUser();
  return user?.warehouse_id ?? null;
};

const isBatchSold = (batch: SalesBatch): boolean => {
  const status = (batch.status ?? "").toString().toUpperCase().trim();
  const category = (batch.sales_category ?? "").toString().toUpperCase().trim();
  return (
    status === "INACTIVE" ||
    status === "SELLED" ||
    status === "SOLD" ||
    category === "SELLED" ||
    category === "SOLD"
  );
};

const getCategoryBadgeStyle = (
  category: string | undefined,
  sold: boolean
): React.CSSProperties => {
  if (sold) return { background: "#f3f4f6", color: "#6b7280" };
  const cat = (category ?? "").toUpperCase();
  switch (cat) {
    case "SELL_NOW":    return { background: "#dcfce7", color: "#166534" };
    case "SELL_SOON":   return { background: "#fef9c3", color: "#854d0e" };
    case "DO_NOT_SELL": return { background: "#fee2e2", color: "#991b1b" };
    default:            return { background: "#f3f4f6", color: "#6b7280" };
  }
};

const badgeStyle: React.CSSProperties = {
  display: "inline-block",
  fontSize: "11px",
  fontWeight: 500,
  padding: "3px 8px",
  borderRadius: "999px",
};

export default function SalesBatches() {
  const warehouseId = getWarehouseIdFromToken();

  const [batches, setBatches] = useState<SalesBatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingBatch, setProcessingBatch] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "SOLD">("ALL");

  const fetchData = async () => {
    setLoading(true);
    try {
      const batchRes = await getSalesBatches();
      console.log("RAW API RESPONSE:", JSON.stringify(batchRes, null, 2));

      // ✅ Handle all possible response shapes — same pattern as ManagerBatches
      let data: SalesBatch[] = [];
      if (Array.isArray(batchRes)) {
        data = batchRes;
      } else if (Array.isArray((batchRes as any)?.data)) {
        data = (batchRes as any).data;
      } else if (Array.isArray((batchRes as any)?.batches)) {
        data = (batchRes as any).batches;
      }

      console.log("Parsed batches:", data);
      setBatches(data);
      setError(null);
    } catch (err: unknown) {
      type AxiosError = { response?: { status?: number; data?: { detail?: string } } };
      const axiosErr = err as AxiosError;
      const status = axiosErr?.response?.status;
      const detail = axiosErr?.response?.data?.detail;
      if (status === 401) setError("Session expired. Please log in again.");
      else if (status === 403) setError("Access denied. You do not have permission.");
      else setError(detail || "Failed to load sales batches. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchData();
  }, []);

  const sellBatch = async (batchId: string) => {
    setProcessingBatch(batchId);
    setError(null);
    try {
      await closeSalesBatch(batchId);
      // ✅ Update both status AND sales_category so isBatchSold() catches it immediately
      setBatches((prev) =>
        prev.map((b) =>
          b.batch_id === batchId
            ? { ...b, status: "INACTIVE", sales_category: "SELLED" }
            : b
        )
      );
    } catch (err: unknown) {
      type AxiosError = { response?: { status?: number; data?: { detail?: string } } };
      const axiosErr = err as AxiosError;
      const status = axiosErr?.response?.status;
      const detail = axiosErr?.response?.data?.detail;
      if (status === 403) setError("Access denied. You cannot close this batch.");
      else setError(detail || "Unable to sell batch. Please try again.");
    } finally {
      setProcessingBatch(null);
    }
  };

  const filteredBatches = batches.filter((b) => {
    const sold = isBatchSold(b);
    if (statusFilter === "SOLD") return sold;
    if (statusFilter === "ACTIVE") return !sold;
    return true; // ALL
  });

  // ✅ Stats computed fresh from batches array every render
  const stats = {
    total: batches.length,
    active: batches.filter((b) => !isBatchSold(b)).length,
    sellNow: batches.filter((b) => {
      const cat = (b.sales_category ?? "").toString().toUpperCase();
      return cat === "SELL_NOW" && !isBatchSold(b);
    }).length,
    sold: batches.filter((b) => isBatchSold(b)).length,
  };

  // ✅ Resolve shelf life from either field name the API might return
  const resolveShelfLife = (batch: SalesBatch): string => {
    const days =
      batch.remaining_shelf_life_days ??
      batch.predicted_remaining_shelf_life_days ??
      null;
    if (days == null) return "N/A";
    return `${days} day${days === 1 ? "" : "s"}`;
  };

  if (loading) {
    return (
      <div className="manager-page">
        <p style={{ color: "#6b7280" }}>Loading sales batches...</p>
      </div>
    );
  }

  if (error && batches.length === 0) {
    return (
      <div className="manager-page">
        <div style={{ padding: "16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "8px", color: "#dc2626" }}>
          <strong>Error:</strong> {error}
        </div>
      </div>
    );
  }

  return (
    <div className="manager-page">

      {/* Header */}
      <div className="manager-header">
        <div>
          <h1>Selling Dashboard</h1>
          <p>Warehouse {warehouseId ?? "Unknown"}</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value as "ALL" | "ACTIVE" | "SOLD")}
          style={{ padding: "8px", borderRadius: "8px", border: "1px solid #d1d5db" }}
        >
          <option value="ALL">All</option>
          <option value="ACTIVE">Active</option>
          <option value="SOLD">Sold</option>
        </select>
      </div>

      {/* Stat cards */}
      <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginBottom: "1.25rem" }}>
        {[
          { label: "Total Batches", value: stats.total },
          { label: "Active",        value: stats.active },
          { label: "Sell Now",      value: stats.sellNow },
          { label: "Sold",          value: stats.sold },
        ].map(({ label, value }) => (
          <div
            key={label}
            style={{ flex: 1, minWidth: "100px", background: "#f9fafb", borderRadius: "8px", padding: "12px 16px" }}
          >
            <div style={{ fontSize: "11px", color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "4px" }}>
              {label}
            </div>
            <div style={{ fontSize: "22px", fontWeight: 500 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Inline error banner */}
      {error && batches.length > 0 && (
        <div style={{ padding: "12px 16px", background: "#fef2f2", border: "1px solid #fca5a5", borderRadius: "8px", color: "#dc2626", marginBottom: "16px" }}>
          {error}
        </div>
      )}

      {/* Table */}
      <div className="table-wrapper">
        <table className="dashboard-table">
          <thead>
            <tr>
              <th>Batch ID</th>
              <th>Fruit</th>
              <th>Quantity (KG)</th>
              <th>Status</th>
              <th>Remaining Shelf Life</th>
              <th>Category</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredBatches.length === 0 ? (
              <tr>
                <td className="empty" colSpan={7}>
                  No batches found for selected filter.
                </td>
              </tr>
            ) : (
              filteredBatches.map((batch) => {
                const sold = isBatchSold(batch);
                const categoryStyle = getCategoryBadgeStyle(batch.sales_category, sold);

                return (
                  <tr key={batch.batch_id}>
                    <td style={{ fontFamily: "monospace", fontSize: "12px", color: "#6b7280" }}>
                      {batch.batch_id}
                    </td>
                    <td style={{ fontWeight: 500 }}>{batch.fruit || "Unknown"}</td>
                    <td>{batch.quantity_kg ?? "—"}</td>
                    <td>
                      <span style={{
                        ...badgeStyle,
                        ...(sold
                          ? { background: "#f3f4f6", color: "#6b7280" }
                          : { background: "#dcfce7", color: "#166534" }),
                      }}>
                        {sold ? "Sold" : "Active"}
                      </span>
                    </td>
                    <td>{resolveShelfLife(batch)}</td>
                    <td>
                      <span style={{ ...badgeStyle, ...categoryStyle }}>
                        {sold
                          ? "Sold"
                          : (batch.sales_category?.replace(/_/g, " ") || "N/A")}
                      </span>
                    </td>
                    <td>
                      {sold ? (
                        <span style={{ color: "#6b7280", fontSize: "12px" }}>Sold</span>
                      ) : (
                        <button
                          className="manager-btn"
                          disabled={processingBatch === batch.batch_id}
                          onClick={() => void sellBatch(batch.batch_id)}
                        >
                          {processingBatch === batch.batch_id ? "Selling..." : "Sell"}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}