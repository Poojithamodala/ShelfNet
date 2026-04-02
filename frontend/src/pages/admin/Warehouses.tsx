import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../../styles/warehouse.css";
import "../../styles/common.css";
import { getWarehouses } from "../../api/warehouse.api";
import AddWarehouseModal from "./AddWarehouseModal";

type Warehouse = {
  warehouse_id: string;
  name: string;
  location: string;
  capacity_kg: number;
  active_batches_count: number;
  status: string;
};

export default function Warehouses() {
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const load = async () => {
    const res = await getWarehouses();
    setWarehouses(res.data);
  };

  useEffect(() => {
    const loadData = async () => {
      await load();
    };

    loadData();
  }, []);

  return (
    <>
      <div className="warehouse-header">
        <h1>Warehouses</h1>
        <button onClick={() => setOpen(true)}>+ Add Warehouse</button>
      </div>

      <table className="dashboard-table">
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
