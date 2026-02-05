import api from "./axios";

export const getAllUsers = () =>
  api.get("/users");

export const getPendingUsers = () =>
  api.get("/users/pending");

export const approveUser = (userId: string) =>
  api.post(`/users/${userId}/approve`);

export const disableUser = (userId: string) =>
  api.post(`/users/${userId}/disable`);
