import { Link } from "react-router-dom";
import "../styles/sidebar.css";

type Props = {
  role: "ADMIN" | "MANAGER" | "SALES";
};

export default function Sidebar({ role }: Props) {
  return (
    <aside className="sidebar">
      <h2 className="logo">ShelfNet</h2>

      {role === "ADMIN" && (
        <>
          <Link to="/admin">Dashboard</Link>
          <Link to="/admin/warehouses">Warehouses - Batches</Link>
          <Link to="/admin/users">Users</Link>
          <Link to="/admin/alerts">Alerts</Link>
        </>
      )}

      {role === "MANAGER" && (
        <>
          <Link to="/manager">Dashboard</Link>
          <Link to="/manager/batches">Batches</Link>
          <Link to="/manager/alerts">Alerts</Link>
        </>
      )}

      {role === "SALES" && (
        <>
          <Link to="/sales">Dashboard</Link>
          <Link to="/sales/batches">Sell Now</Link>
          <Link to="/sales/reports">Reports</Link>
        </>
      )}
    </aside>
  );
}
