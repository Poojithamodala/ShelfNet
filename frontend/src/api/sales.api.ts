import api from "./axios";

export const getSalesKpis = () => api.get("/sales/kpis");
export const getSalesBatches = () => api.get("/sales/batches");
export const closeSalesBatch = (batchId: string) => api.post(`/batches/${batchId}/close`);
export const getSalesRecommendations = () => api.get("/sales/recommendations");
export const getSalesExpiryReport = () => api.get("/sales/reports/expiry");