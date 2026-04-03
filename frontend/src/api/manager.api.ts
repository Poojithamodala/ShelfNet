import api from "./axios";

export const getManagerKpis = (warehouseId: string) =>
  api.get(`/manager/${warehouseId}/kpis`);

export const getManagerBatches = (warehouseId: string) =>
  api.get(`/manager/${warehouseId}/batches`);

export const getManagerAlerts = (warehouseId: string) =>
  api.get(`/manager/${warehouseId}/alerts`);

export const resolveManagerAlert = (alertId: string) =>
  api.post(`/manager/alerts/${alertId}/resolve`);

export type SensorReadingPayload = {
  temperature_c?:    number;
  humidity_percent?: number;
  ethylene_ppm?:     number;
  co2_ppm?:          number;
  o2_percent?:       number;
};

export type ManagerBatchPayload = {
  fruit:                    string;
  quantity_kg:              number;
  arrival_date:             string;
  expected_shelf_life_days: number;
  warehouse_id:             string;
  sensor_reading?:          SensorReadingPayload;
};

export const createManagerBatch = (batchData: ManagerBatchPayload) =>
  api.post(`/manager/${batchData.warehouse_id}/batches/create`, batchData);