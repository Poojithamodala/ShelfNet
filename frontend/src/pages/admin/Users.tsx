import { useEffect, useState } from "react";
import {
  getAllUsers,
  approveUser,
  disableUser,
} from "../../api/users.api";
import "../../styles/users.css";

type User = {
  user_id: string;
  name: string;
  email: string;
  role: string;
  warehouse_id?: string;
  status: string;
};

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  const loadUsers = async () => {
    setLoading(true);
    const res = await getAllUsers();
    setUsers(res.data);
    setLoading(false);
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const pendingUsers = users.filter((u) => u.status === "PENDING");
  const otherUsers = users.filter((u) => u.status !== "PENDING");

  const handleApprove = async (user: User) => {
    const ok = window.confirm(
      `Approve access for ${user.name} (${user.role})?`
    );
    if (!ok) return;

    await approveUser(user.user_id);
    loadUsers();
  };

  const handleDisable = async (user: User) => {
    const ok = window.confirm(
      `Disable ${user.name}? They will lose access immediately.`
    );
    if (!ok) return;

    await disableUser(user.user_id);
    loadUsers();
  };

  if (loading) return <p className="loading">Loading users...</p>;

  return (
    <div className="users-page">
      <h2>User Management</h2>

      {/* 🔔 Pending Users */}
      {pendingUsers.length > 0 && (
        <>
          <h3 className="section-title">Pending Approvals</h3>
          <UsersTable
            users={pendingUsers}
            onApprove={handleApprove}
            onDisable={handleDisable}
          />
        </>
      )}

      {/* 👥 All Other Users */}
      <h3 className="section-title">All Users</h3>
      <UsersTable
        users={otherUsers}
        onApprove={handleApprove}
        onDisable={handleDisable}
      />
    </div>
  );
}

function UsersTable({
  users,
  onApprove,
  onDisable,
}: {
  users: User[];
  onApprove: (u: User) => void;
  onDisable: (u: User) => void;
}) {
  return (
    <table className="users-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Email</th>
          <th>Role</th>
          <th>Warehouse</th>
          <th>Status</th>
          <th>Actions</th>
        </tr>
      </thead>

      <tbody>
        {users.map((u) => (
          <tr key={u.user_id} className={u.status.toLowerCase()}>
            <td>{u.name}</td>
            <td>{u.email}</td>
            <td>{u.role}</td>
            <td>{u.warehouse_id || "—"}</td>
            <td>
              <span className={`status ${u.status}`}>
                {u.status}
              </span>
            </td>
            <td className="actions">
              {u.status === "PENDING" && (
                <button
                  className="approve"
                  onClick={() => onApprove(u)}
                >
                  Approve
                </button>
              )}

              {u.role !== "ADMIN" && u.status === "ACTIVE" && (
                <button
                  className="disable"
                  onClick={() => onDisable(u)}
                >
                  Disable
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
