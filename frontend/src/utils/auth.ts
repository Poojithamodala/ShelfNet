export type AuthUser = {
  user_id: string;
  role: string;
  warehouse_id?: string;
};

export const saveAuth = (token: string, user: AuthUser) => {
  localStorage.setItem("token", token);
  localStorage.setItem("user", JSON.stringify(user));
};

export const getUser = (): AuthUser | null => {
  const u = localStorage.getItem("user");
  return u ? (JSON.parse(u) as AuthUser) : null;
};

export const logout = () => {
  localStorage.clear();
  window.location.href = "/login";
};
