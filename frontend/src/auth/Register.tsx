import { useState } from "react";
import axios from "axios";
import "../styles/auth.css";

export default function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    role: "MANAGER",
    warehouse_id: ""
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const submit = async () => {
    try {
      await axios.post("http://127.0.0.1:8000/users", {
        name: form.name,
        email: form.email,
        role: form.role,
        warehouse_id: form.warehouse_id
      });

      alert("Registration submitted. Await admin approval.");
    } catch (err: unknown) {
      type AxiosError = { response?: { data?: { detail?: string } } };
      const message = (err as AxiosError)?.response?.data?.detail || "Registration failed";
      alert(message);
    }
  };

  return (
    <div className="auth-form">
      <h2>Register</h2>

      <input
        name="name"
        placeholder="Full Name"
        onChange={handleChange}
      />

      <input
        name="email"
        placeholder="Email"
        onChange={handleChange}
      />

      <select name="role" onChange={handleChange}>
        <option value="MANAGER">Manager</option>
        <option value="SALES">Sales</option>
      </select>

      <input
        name="warehouse_id"
        placeholder="Warehouse ID"
        onChange={handleChange}
      />

      <button onClick={submit}>Submit Request</button>
    </div>
  );
}
