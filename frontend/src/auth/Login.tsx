import { useState } from "react";
import { loginUser } from "../api/auth.api";
import { saveAuth } from "../utils/auth";
import { useNavigate } from "react-router-dom";
import "../styles/auth.css";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await loginUser(email, password);
      saveAuth(res.data.access_token, res.data.user);

      const role = res.data.user.role;
      if (role === "ADMIN") navigate("/admin");
      else if (role === "MANAGER") navigate("/manager");
      else navigate("/sales");
    } catch (err: any) {
      const detail = err.response?.data?.detail;

      if (detail === "Password not set. Please complete account setup.") {
        navigate("/set-password", { state: { email } });
      } else {
        alert(detail || "Login failed");
      }
    }
  };

  return (
    <div className="auth-form">
      <div className="auth-card">
        <h2>Welcome to ShelfNet</h2>
        <p className="auth-subtitle">
          Smart monitoring for perishable goods
        </p>

        <input
          type="email"
          placeholder="Email address"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button onClick={handleLogin}>Login</button>

        <div className="auth-footer">
          <span>New user?</span>
          <a href="/register">Request access</a>
        </div>
      </div>
    </div>
  );
}
