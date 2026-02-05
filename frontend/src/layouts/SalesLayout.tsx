import { Outlet } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

export default function SalesLayout() {
  return (
    <div className="app-layout">
      <Sidebar role="SALES" />
      <div className="content-area">
        <Topbar />
        <div className="page-content">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
