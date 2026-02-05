import api from "./axios";

export const getWarehouses = () =>
  api.get("/warehouses");

export const createWarehouse = (data: {
  name: string;
  location: string;
  capacity_kg: number;
}) =>
  api.post("/warehouses", data);
