import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api from "../../api/axios";
import "../../styles/batches.css";
import "../../styles/common.css";

type WarehouseBatch = {
  batch_id: string;
  fruit: string;
  quantity_kg: number;
  status: string;
  predicted_remaining_shelf_life_days?: number;
};

export default function WarehouseBatches() {
  const { warehouseId } = useParams();
  const [batches, setBatches] = useState<WarehouseBatch[]>([]);

  useEffect(() => {
    api
      .get(`/batches?warehouse_id=${warehouseId}`)
      .then((res) => setBatches(res.data));
  }, [warehouseId]);

  return (
    <>
      <h1>Warehouse {warehouseId} – Batches</h1>

      <table className="dashboard-table">
        <thead>
          <tr>
            <th>Batch ID</th>
            <th>Fruit</th>
            <th>Quantity (kg)</th>
            <th>Status</th>
            <th>Remaining Shelf Life</th>
          </tr>
        </thead>

        <tbody>
          {batches.map((b) => (
            <tr key={b.batch_id}>
              <td>{b.batch_id}</td>
              <td>{b.fruit}</td>
              <td>{b.quantity_kg}</td>
              <td>{b.status}</td>
              <td>
                {b.predicted_remaining_shelf_life_days
                  ? `${b.predicted_remaining_shelf_life_days.toFixed(1)} days`
                  : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}
