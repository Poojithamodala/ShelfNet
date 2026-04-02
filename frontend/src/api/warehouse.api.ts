import api from "./axios";

export const getWarehouses = () =>
  api.get("/warehouses");

export const getWarehouseById = (warehouseId: string) =>
  api.get(`/warehouses/${warehouseId}`);

export const createWarehouse = (data: {
  name: string;
  location: string;
  capacity_kg: number;
}) =>
  api.post("/warehouses", data);
