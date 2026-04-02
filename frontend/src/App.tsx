import { BrowserRouter, Routes, Route } from "react-router-dom";

import AdminLayout from "./layouts/AdminLayout";
import ManagerLayout from "./layouts/ManagerLayout";
import SalesLayout from "./layouts/SalesLayout";
import Login from "./auth/Login";
import ProtectedRoute from "./auth/ProtectedRoute";
import Home from "./pages/home/Home";
import Register from "./auth/Register";
import SetPassword from "./auth/SetPassword";
import AdminDashboard from "./pages/admin/AdminDashboard";
import Warehouses from "./pages/admin/Warehouses";
import AdminUsers from "./pages/admin/Users";
import AdminAlerts from "./pages/admin/AdminAlerts";
import WarehouseBatches from "./pages/admin/WarehouseBatches";
import ManagerDashboard from "./pages/manager/ManagerDashboard";
import ManagerBatches from "./pages/manager/ManagerBatches";
import ManagerAlerts from "./pages/manager/ManagerAlerts";
import SalesDashboard from "./pages/sales/SalesDashboard";
import SalesBatches from "./pages/sales/SalesBatches";
import SalesReports from "./pages/sales/SalesReports";


export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/set-password" element={<SetPassword />} />
        
        <Route path="/admin" element={<AdminLayout />}>
          <Route index element={<AdminDashboard />} />
          <Route path="warehouses" element={<Warehouses />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/alerts" element={<AdminAlerts />} />
          <Route path="/admin/warehouses/:warehouseId/batches" element={<WarehouseBatches />} />
        </Route>

        <Route
          path="/manager"
          element={
            <ProtectedRoute allowedRoles={["MANAGER"]}>
              <ManagerLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<ManagerDashboard />} />
          <Route path="batches" element={<ManagerBatches />} />
          <Route path="alerts" element={<ManagerAlerts />} />
        </Route>

        <Route
          path="/sales"
          element={
            <ProtectedRoute allowedRoles={["SALES"]}>
              <SalesLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<SalesDashboard />} />
          <Route path="batches" element={<SalesBatches />} />
          <Route path="reports" element={<SalesReports />} />
        </Route>

      </Routes>
    </BrowserRouter>
  );
}
