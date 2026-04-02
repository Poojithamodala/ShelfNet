import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import "../styles/layout.css";
import { getUser } from "../utils/auth";

export default function AdminLayout() {
  const user = getUser();
  const role = (user?.role as "ADMIN" | "MANAGER" | "SALES") || "ADMIN";

  return (
    <div className="app-layout">
      <Sidebar role={role} />

      <div className="main-content">
        <Topbar />
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
