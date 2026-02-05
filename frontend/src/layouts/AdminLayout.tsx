import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";
import "../styles/layout.css";
import { getUser } from "../utils/auth";

export default function AdminLayout() {
  const user = getUser();

  return (
    <div className="app-layout">
      <Sidebar role={user.role} />

      <div className="main-content">
        <Topbar />
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
