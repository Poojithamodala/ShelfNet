import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { setPassword } from "../api/auth.api";
import "../styles/auth.css";

export default function SetPassword() {
  const navigate = useNavigate();
  const location = useLocation();

  const email = location.state?.email;

  const [password, setPasswordInput] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  if (!email) {
    return (
      <div className="auth-form">
        <div className="auth-card">
          <h2>Error</h2>
          <p className="auth-subtitle">
            Invalid password setup request.
          </p>
        </div>
      </div>
    );
  }

  const handleSetPassword = async () => {
    if (password.length < 6) {
      alert("Password must be at least 6 characters");
      return;
    }

    if (password !== confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    try {
      await setPassword(email, password);
      alert("Password set successfully. Please login.");
      navigate("/login");
    } catch (err: unknown) {
      type AxiosError = { response?: { data?: { detail?: string } } };
      const message = (err as AxiosError)?.response?.data?.detail || "Failed to set password";
      alert(message);
    }
  };

  return (
    <div className="auth-form">
      <div className="auth-card">
        <h2>Set Your Password</h2>
        <p className="auth-subtitle">
          Complete account setup for ShelfNet
        </p>

        <input
          type="email"
          value={email}
          disabled
        />

        <input
          type="password"
          placeholder="New password"
          value={password}
          onChange={(e) => setPasswordInput(e.target.value)}
        />

        <input
          type="password"
          placeholder="Confirm password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        <button onClick={handleSetPassword}>
          Set Password
        </button>

        <div className="auth-footer">
          <a href="/login">Back to Login</a>
        </div>
      </div>
    </div>
  );
}
