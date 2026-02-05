import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

export default function ManagerLayout() {
  return (
    <div className="app-layout">
      <Sidebar role="MANAGER" />
      <div className="content-area">
        <Topbar />
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
