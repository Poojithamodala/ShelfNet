import { useState, useEffect } from "react";
import axios from "axios";
import "../styles/auth.css";
 
type Warehouse = {
  warehouse_id: string;
  name: string;
  location: string;
};
 
export default function Register() {
  const [form, setForm] = useState({
    name: "",
    email: "",
    role: "MANAGER",
    warehouse_id: ""
  });
 
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [loadingWarehouses, setLoadingWarehouses] = useState(true);
 
  useEffect(() => {
    const fetchWarehouses = async () => {
      try {
        const res = await axios.get("http://127.0.0.1:8000/public/warehouses");
        setWarehouses(res.data);
        // ✅ No auto-select — placeholder shows first
      } catch (err) {
        console.error("Failed to load warehouses", err);
      } finally {
        setLoadingWarehouses(false);
      }
    };
 
    fetchWarehouses();
  }, []);
 
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };
 
  const submit = async () => {
    if (!form.warehouse_id) {
      alert("Please select a warehouse.");
      return;
    }
 
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
      const message =
        (err as AxiosError)?.response?.data?.detail || "Registration failed";
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
 
      <select name="role" onChange={handleChange} value={form.role}>
        <option value="MANAGER">Manager</option>
        <option value="SALES">Sales</option>
      </select>
 
      {loadingWarehouses ? (
        <select disabled>
          <option>Loading warehouses...</option>
        </select>
      ) : warehouses.length === 0 ? (
        <select disabled>
          <option>No warehouses available</option>
        </select>
      ) : (
        <select
          name="warehouse_id"
          onChange={handleChange}
          value={form.warehouse_id}
        >
          <option value="" disabled>-- Select your Warehouse --</option>
          {warehouses.map((wh) => (
            <option key={wh.warehouse_id} value={wh.warehouse_id}>
              {wh.name} — {wh.location} ({wh.warehouse_id})
            </option>
          ))}
        </select>
      )}
 
      <button onClick={submit}>Submit Request</button>
    </div>
  );
}