import { useEffect, useState, type FormEvent } from "react";
import { getUser } from "../../utils/auth";
import { getManagerBatches, createManagerBatch } from "../../api/manager.api";
import { getWarehouseById } from "../../api/warehouse.api";
import "../../styles/manager.css";
import "../../styles/common.css";

export default function ManagerBatches() {
  const user = getUser();
  const warehouseId = user?.warehouse_id;

  type Batch = {
    batch_id: string;
    fruit?: string;
    quantity_kg?: number;
    status?: string;
    predicted_remaining_shelf_life_days?: number;
  };

  type Warehouse = {
    warehouse_id?: string;
    name?: string;
  };

  type NewBatch = {
    fruit: string;
    quantity_kg: string;
    arrival_date: string;
  };

  const [batches, setBatches] = useState<Batch[]>([]);
  const [warehouse, setWarehouse] = useState<Warehouse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddBatch, setShowAddBatch] = useState(false);
  const [newBatch, setNewBatch] = useState<NewBatch>({
    fruit: "",
    quantity_kg: "",
    arrival_date: ""
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<"ALL" | "ACTIVE" | "INACTIVE">("ALL");

  useEffect(() => {
    const fetchData = async () => {
      if (!warehouseId) {
        setError("No warehouse assigned to this manager.");
        setLoading(false);
        return;
      }

      setLoading(true);

      try {
        const [batchRes, warehouseRes] = await Promise.all([
          getManagerBatches(warehouseId),
          getWarehouseById(warehouseId)
        ]) as [{ data: Batch[] }, { data: Warehouse }];

        setBatches(batchRes.data);
        setWarehouse(warehouseRes.data);
        setError(null);
      } catch (err: unknown) {
        type AxiosError = { response?: { data?: { detail?: string } } };
        const message = (err as AxiosError)?.response?.data?.detail || "Could not load batches";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [warehouseId]);

  const handleAddBatchChange = (field: string, value: string) => {
    setNewBatch((prev) => ({ ...prev, [field]: value }));
  };

  const handleSubmitNewBatch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!warehouseId) {
      setFormError("No warehouse assigned");
      return;
    }

    if (!newBatch.fruit || !newBatch.quantity_kg || !newBatch.arrival_date) {
      setFormError("Please fill all fields.");
      return;
    }

    const batchPayload = {
      fruit: newBatch.fruit,
      quantity_kg: Number(newBatch.quantity_kg),
      arrival_date: newBatch.arrival_date,
      expected_shelf_life_days: 30,
      warehouse_id: warehouseId
    };

    try {
      setFormError(null);
      await createManagerBatch(batchPayload);
      setSuccessMessage("Batch added successfully.");
      setShowAddBatch(false);
      setNewBatch({ fruit: "", quantity_kg: "", arrival_date: "" });

      const [batchRes, warehouseRes] = await Promise.all([
        getManagerBatches(warehouseId),
        getWarehouseById(warehouseId)
      ]) as [{ data: Batch[] }, { data: Warehouse }];
      setBatches(batchRes.data);
      setWarehouse(warehouseRes.data);
    } catch (err: unknown) {
      type AxiosError = { response?: { data?: { detail?: string } } };
      const message = (err as AxiosError)?.response?.data?.detail || "Failed to add batch";
      setFormError(message);
    }
  };

  const filteredBatches = batches.filter((batch) => {
    if (statusFilter === "ALL") return true;
    return batch.status === statusFilter;
  });

  if (loading) return <p>Loading batches...</p>;
  if (error) return <p>{error}</p>;

  return (
    <div className="manager-page">
      <div className="manager-header">
        <div>
          <h1>Warehouse {warehouseId} – Batches</h1>

          {/* ✅ FIXED TEMPLATE STRING */}
          <p>
            {warehouse?.name
              ? `${warehouse.name} (${warehouseId})`
              : `Warehouse ${warehouseId}`}
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <select
            value={statusFilter}
            onChange={(e) =>
              setStatusFilter(e.target.value as "ALL" | "ACTIVE" | "INACTIVE")
            }
            style={{ padding: "8px", borderRadius: "8px", border: "1px solid #d1d5db" }}
          >
            <option value="ALL">All</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Selled</option>
          </select>

          <button
            className="manager-btn"
            onClick={() => {
              setShowAddBatch(true);
              setFormError(null);
              setSuccessMessage(null);
            }}
          >
            Add Batch
          </button>
        </div>
      </div>

      {successMessage && <p style={{ color: "green" }}>{successMessage}</p>}

      {showAddBatch && (
        <div
          className="manager-page"
          style={{
            background: "rgba(0,0,0,0.1)",
            padding: "12px",
            borderRadius: "10px",
            marginBottom: "18px"
          }}
        >
          <h2>Add new batch</h2>

          <form onSubmit={handleSubmitNewBatch}>
            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
              <input
                type="text"
                placeholder="Fruit"
                value={newBatch.fruit}
                onChange={(e) => handleAddBatchChange("fruit", e.target.value)}
                style={{ padding: "8px", width: "200px" }}
              />

              <input
                type="number"
                placeholder="Quantity (kg)"
                value={newBatch.quantity_kg}
                onChange={(e) => handleAddBatchChange("quantity_kg", e.target.value)}
                style={{ padding: "8px", width: "200px" }}
              />

              <input
                type="date"
                value={newBatch.arrival_date}
                onChange={(e) => handleAddBatchChange("arrival_date", e.target.value)}
                style={{ padding: "8px", width: "200px" }}
              />
            </div>

            {formError && (
              <p style={{ color: "red", marginTop: "8px" }}>{formError}</p>
            )}

            <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
              <button className="manager-btn" type="submit">
                Save
              </button>

              <button
                type="button"
                className="manager-btn"
                style={{ background: "#6b7280" }}
                onClick={() => setShowAddBatch(false)}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

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
            </tr>
          </thead>

          <tbody>
            {filteredBatches.length === 0 ? (
              <tr>
                <td className="empty" colSpan={6}>
                  No batches found for selected status.
                </td>
              </tr>
            ) : (
              filteredBatches.map((batch) => (
                <tr key={batch.batch_id}>
                  <td>{batch.batch_id}</td>
                  <td>{batch.fruit || "Unknown"}</td>
                  <td>{batch.quantity_kg ?? "-"}</td>
                  <td>{batch.status || "N/A"}</td>

                  {/* ✅ FIXED TEMPLATE STRING */}
                  <td>
                    {batch.predicted_remaining_shelf_life_days != null
                      ? `${batch.predicted_remaining_shelf_life_days} day${
                          batch.predicted_remaining_shelf_life_days === 1 ? "" : "s"
                        }`
                      : "N/A"}
                  </td>

                  <td>
                    {batch.status === "INACTIVE" ? "SELLED" : "ACTIVE"}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}