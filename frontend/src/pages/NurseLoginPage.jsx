import { useState } from "react";
import { nurseLogin } from "../services/api";

export default function NurseLoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await nurseLogin(username.trim(), password);
      onLogin(data);
    } catch (err) {
      setError("Invalid username or password. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="main-container" style={{ maxWidth: "400px" }}>
      <div className="card" style={{ padding: "2rem" }}>
        <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
          <div style={{ fontSize: "2.5rem" }}>🩺</div>
          <h1 style={{ fontSize: "1.3rem", fontWeight: "700", color: "#005691", marginTop: "0.5rem" }}>
            Nurse Login
          </h1>
          <p style={{ fontSize: "0.85rem", color: "#6b7280", marginTop: "0.25rem" }}>
            MediVoice Triage Dashboard
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <label style={{ fontSize: "0.85rem", fontWeight: "600", color: "#374151" }}>
            Username
          </label>
          <input
            id="nurse-username"
            className="input-field"
            type="text"
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="admin"
            autoComplete="username"
            required
          />
          <label style={{ fontSize: "0.85rem", fontWeight: "600", color: "#374151" }}>
            Password
          </label>
          <input
            id="nurse-password"
            className="input-field"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="••••••••"
            autoComplete="current-password"
            required
          />
          {error && (
            <div style={{ color: "#dc2626", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
              {error}
            </div>
          )}
          <button className="btn btn-primary" type="submit"
            id="nurse-login-btn"
            style={{ width: "100%", padding: "0.8rem" }}
            disabled={loading}>
            {loading ? "Logging in..." : "Sign In"}
          </button>
        </form>
        <p style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "1rem", textAlign: "center" }}>
          Demo: admin / admin1234
        </p>
      </div>
    </div>
  );
}
