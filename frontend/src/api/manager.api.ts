import api from "./axios";

export const getManagerKpis = (warehouseId: string) =>
  api.get(`/manager/${warehouseId}/kpis`);

export const getManagerBatches = (warehouseId: string) =>
  api.get(`/manager/${warehouseId}/batches`);

export const getManagerAlerts = (warehouseId: string) =>
  api.get(`/manager/${warehouseId}/alerts`);

export const resolveManagerAlert = (alertId: string) =>
  api.post(`/manager/alerts/${alertId}/resolve`);

export type ManagerBatchPayload = {
  fruit: string;
  quantity_kg: number;
  arrival_date: string;
  expected_shelf_life_days: number;
  warehouse_id: string;
};

export const createManagerBatch = (batchData: ManagerBatchPayload) =>
  api.post(`/batches`, batchData);
