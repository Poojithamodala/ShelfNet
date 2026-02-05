import "../styles/layout.css";
import { logout } from "../utils/auth";

export default function Topbar() {
  return (
    <header className="topbar">
      <span>Cold Chain Intelligence</span>
      <button onClick={logout}>Logout</button>
    </header>
  );
}
