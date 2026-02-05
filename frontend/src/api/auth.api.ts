import api from "./axios";

export const loginUser = (email: string, password: string) =>
  api.post("/auth/login", { email, password });

export const setPassword = (email: string, password: string) =>
  api.post("/auth/set-password", { email, password });
