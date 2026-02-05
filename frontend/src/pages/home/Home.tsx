import { Link } from "react-router-dom";
import "../../styles/home.css";

export default function Home() {
  return (
    <div className="home-container">
      <h1>ShelfNet</h1>
      <p>AI-powered Cold Chain Monitoring & Shelf-Life Intelligence</p>

      <div className="home-actions">
        <Link to="/login">
          <button className="primary">Login</button>
        </Link>

        <Link to="/register">
          <button className="secondary">Register</button>
        </Link>
      </div>
    </div>
  );
}
