import { useEffect, useState, type FormEvent } from "react";
import { getUser } from "../../utils/auth";
import { getManagerBatches, createManagerBatch, type ManagerBatchPayload } from "../../api/manager.api";
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
    // required
    fruit: string;
    quantity_kg: string;
    arrival_date: string;
    // optional sensor readings
    temperature_c: string;
    humidity_percent: string;
    ethylene_ppm: string;
    co2_ppm: string;
    o2_percent: string;
  };

  const [batches, setBatches] = useState<Batch[]>([]);
  const [warehouse, setWarehouse] = useState<Warehouse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddBatch, setShowAddBatch] = useState(false);
  const [showSensorFields, setShowSensorFields] = useState(false);
  const [newBatch, setNewBatch] = useState<NewBatch>({
    fruit: "",
    quantity_kg: "",
    arrival_date: "",
    temperature_c: "",
    humidity_percent: "",
    ethylene_ppm: "",
    co2_ppm: "",
    o2_percent: "",
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
          getWarehouseById(warehouseId),
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

  const resetForm = () => {
    setNewBatch({
      fruit: "",
      quantity_kg: "",
      arrival_date: "",
      temperature_c: "",
      humidity_percent: "",
      ethylene_ppm: "",
      co2_ppm: "",
      o2_percent: "",
    });
    setShowSensorFields(false);
    setFormError(null);
  };

  const handleSubmitNewBatch = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!warehouseId) {
      setFormError("No warehouse assigned");
      return;
    }

    if (!newBatch.fruit || !newBatch.quantity_kg || !newBatch.arrival_date) {
      setFormError("Please fill all required fields.");
      return;
    }

    // Build base payload
    const batchPayload: ManagerBatchPayload = {
      fruit: newBatch.fruit,
      quantity_kg: Number(newBatch.quantity_kg),
      arrival_date: newBatch.arrival_date,
      expected_shelf_life_days: 30,
      warehouse_id: warehouseId,
    };

    // Attach sensor readings only if provided
    const sensorReading: Record<string, number> = {};

    if (newBatch.temperature_c !== "")
      sensorReading.temperature_c = Number(newBatch.temperature_c);
    if (newBatch.humidity_percent !== "")
      sensorReading.humidity_percent = Number(newBatch.humidity_percent);
    if (newBatch.ethylene_ppm !== "")
      sensorReading.ethylene_ppm = Number(newBatch.ethylene_ppm);
    if (newBatch.co2_ppm !== "")
      sensorReading.co2_ppm = Number(newBatch.co2_ppm);
    if (newBatch.o2_percent !== "")
      sensorReading.o2_percent = Number(newBatch.o2_percent);

    if (Object.keys(sensorReading).length > 0) {
      batchPayload.sensor_reading = sensorReading;
    }

    try {
      setFormError(null);
      await createManagerBatch(batchPayload);
      setSuccessMessage("Batch added successfully.");
      setShowAddBatch(false);
      resetForm();

      const [batchRes, warehouseRes] = await Promise.all([
        getManagerBatches(warehouseId),
        getWarehouseById(warehouseId),
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

      {successMessage && (
        <p style={{ color: "green", marginBottom: "12px" }}>{successMessage}</p>
      )}

      {/* ── ADD BATCH FORM ── */}
      {showAddBatch && (
        <div
          style={{
            background: "#f9fafb",
            border: "1px solid #e5e7eb",
            padding: "20px",
            borderRadius: "12px",
            marginBottom: "24px",
          }}
        >
          <h2 style={{ marginBottom: "16px" }}>Add New Batch</h2>

          <form onSubmit={handleSubmitNewBatch}>

            {/* ── REQUIRED FIELDS ── */}
            <p style={{ fontSize: "12px", fontWeight: 600, color: "#6b7280", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Batch Details <span style={{ color: "#ef4444" }}>*</span>
            </p>

            <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", marginBottom: "16px" }}>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "12px", color: "#374151" }}>Fruit <span style={{ color: "#ef4444" }}>*</span></label>
                <input
                  type="text"
                  placeholder="e.g. Mango"
                  value={newBatch.fruit}
                  onChange={(e) => handleAddBatchChange("fruit", e.target.value)}
                  style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #d1d5db", width: "180px" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "12px", color: "#374151" }}>Quantity (kg) <span style={{ color: "#ef4444" }}>*</span></label>
                <input
                  type="number"
                  placeholder="e.g. 200"
                  value={newBatch.quantity_kg}
                  onChange={(e) => handleAddBatchChange("quantity_kg", e.target.value)}
                  style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #d1d5db", width: "180px" }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                <label style={{ fontSize: "12px", color: "#374151" }}>Arrival Date <span style={{ color: "#ef4444" }}>*</span></label>
                <input
                  type="date"
                  value={newBatch.arrival_date}
                  onChange={(e) => handleAddBatchChange("arrival_date", e.target.value)}
                  style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #d1d5db", width: "180px" }}
                />
              </div>
            </div>

            {/* ── OPTIONAL SENSOR READINGS TOGGLE ── */}
            <div style={{ marginBottom: "12px" }}>
              <button
                type="button"
                onClick={() => setShowSensorFields((prev) => !prev)}
                style={{
                  background: "none",
                  border: "1px dashed #9ca3af",
                  borderRadius: "8px",
                  padding: "6px 14px",
                  fontSize: "13px",
                  color: "#6b7280",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>{showSensorFields ? "▾" : "▸"}</span>
                {showSensorFields ? "Hide Sensor Readings" : "Add Sensor Readings (optional — used for shelf life prediction)"}
              </button>
            </div>

            {/* ── OPTIONAL SENSOR FIELDS ── */}
            {showSensorFields && (
              <div
                style={{
                  background: "#f0f9ff",
                  border: "1px solid #bae6fd",
                  borderRadius: "10px",
                  padding: "16px",
                  marginBottom: "16px",
                }}
              >
                <p style={{ fontSize: "12px", color: "#0369a1", marginBottom: "12px", fontWeight: 500 }}>
                  📡 Sensor Readings — leave blank to skip prediction at creation
                </p>

                <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#374151" }}>Temperature (°C)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 18.5"
                      value={newBatch.temperature_c}
                      onChange={(e) => handleAddBatchChange("temperature_c", e.target.value)}
                      style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #bae6fd", width: "160px" }}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#374151" }}>Humidity (%)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 85.0"
                      value={newBatch.humidity_percent}
                      onChange={(e) => handleAddBatchChange("humidity_percent", e.target.value)}
                      style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #bae6fd", width: "160px" }}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#374151" }}>Ethylene (ppm)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g. 0.45"
                      value={newBatch.ethylene_ppm}
                      onChange={(e) => handleAddBatchChange("ethylene_ppm", e.target.value)}
                      style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #bae6fd", width: "160px" }}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#374151" }}>CO₂ (ppm)</label>
                    <input
                      type="number"
                      step="0.1"
                      placeholder="e.g. 420.0"
                      value={newBatch.co2_ppm}
                      onChange={(e) => handleAddBatchChange("co2_ppm", e.target.value)}
                      style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #bae6fd", width: "160px" }}
                    />
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                    <label style={{ fontSize: "12px", color: "#374151" }}>O₂ (%)</label>
                    <input
                      type="number"
                      step="0.01"
                      placeholder="e.g. 20.9"
                      value={newBatch.o2_percent}
                      onChange={(e) => handleAddBatchChange("o2_percent", e.target.value)}
                      style={{ padding: "8px 12px", borderRadius: "8px", border: "1px solid #bae6fd", width: "160px" }}
                    />
                  </div>
                </div>
              </div>
            )}

            {formError && (
              <p style={{ color: "#ef4444", marginBottom: "10px", fontSize: "13px" }}>{formError}</p>
            )}

            <div style={{ display: "flex", gap: "8px" }}>
              <button className="manager-btn" type="submit">
                Save Batch
              </button>
              <button
                type="button"
                className="manager-btn"
                style={{ background: "#6b7280" }}
                onClick={() => {
                  setShowAddBatch(false);
                  resetForm();
                }}
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ── BATCHES TABLE ── */}
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