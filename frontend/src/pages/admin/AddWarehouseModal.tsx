import { useState } from "react";
import { createWarehouse } from "../../api/warehouse.api";
import "../../styles/warehouse.css";

export default function AddWarehouseModal({
  onClose,
  onCreated,
}: {
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({
    name: "",
    location: "",
    capacity_kg: 0,
  });

  const submit = async () => {
    await createWarehouse(form);
    onCreated();
    onClose();
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <h2>Add Warehouse</h2>

        <input
          placeholder="Warehouse Name"
          onChange={e => setForm({ ...form, name: e.target.value })}
        />

        <input
          placeholder="Location"
          onChange={e => setForm({ ...form, location: e.target.value })}
        />

        <input
          type="number"
          placeholder="Capacity (kg)"
          onChange={e =>
            setForm({ ...form, capacity_kg: Number(e.target.value) })
          }
        />

        <div className="modal-actions">
          <button className="secondary" onClick={onClose}>
            Cancel
          </button>
          <button onClick={submit}>Create</button>
        </div>
      </div>
    </div>
  );
}
