import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../styles/warehouse.css";
import { getWarehouses } from "../../api/warehouse.api";
import AddWarehouseModal from "./AddWarehouseModal";

export default function Warehouses() {
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    const res = await getWarehouses();
    setWarehouses(res.data);
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <>
      <div className="warehouse-header">
        <h1>Warehouses</h1>
        <button onClick={() => setOpen(true)}>+ Add Warehouse</button>
      </div>

      <table className="warehouse-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Location</th>
            <th>Capacity (kg)</th>
            <th>Active Batches</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {warehouses.map((w) => (
            <tr
              key={w.warehouse_id}
              className="clickable-row"
              onClick={() =>
                navigate(`/admin/warehouses/${w.warehouse_id}/batches`)
              }
            >
              <td>{w.warehouse_id}</td>
              <td>{w.name}</td>
              <td>{w.location}</td>
              <td>{w.capacity_kg}</td>
              <td><strong>{w.active_batches_count ?? 0}</strong></td>
              <td>
                <span className={`status ${w.status.toLowerCase()}`}>
                  {w.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {open && (
        <AddWarehouseModal
          onClose={() => setOpen(false)}
          onCreated={load}
        />
      )}
    </>
  );
}
