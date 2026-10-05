import { useState } from "react";
import PatientPage from "./pages/PatientPage";
import NurseLoginPage from "./pages/NurseLoginPage";
import NurseDashboardPage from "./pages/NurseDashboardPage";
import "./index.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("patient"); // patient | nurse
  const [nurseInfo, setNurseInfo] = useState(null);

  const handleNurseLogin = (data) => {
    setNurseInfo(data);
  };

  const handleNurseLogout = () => {
    setNurseInfo(null);
  };

  return (
    <>
      <header className="app-header">
        <div className="brand-title">
          <span>🏥</span>
          MediVoice
          <span className="team-badge">Team MediVoice</span>
        </div>
        <nav className="nav-tabs" aria-label="Main navigation">
          <button
            id="tab-patient"
            className={`nav-tab ${activeTab === "patient" ? "active" : ""}`}
            onClick={() => setActiveTab("patient")}
            aria-selected={activeTab === "patient"}
          >
            Patient Intake
          </button>
          <button
            id="tab-nurse"
            className={`nav-tab ${activeTab === "nurse" ? "active" : ""}`}
            onClick={() => setActiveTab("nurse")}
            aria-selected={activeTab === "nurse"}
          >
            Nurse Dashboard
          </button>
        </nav>
      </header>

      <main>
        <div style={{ display: activeTab === "patient" ? "block" : "none" }}>
          <PatientPage />
        </div>
        <div style={{ display: activeTab === "nurse" ? "block" : "none" }}>
          {nurseInfo
            ? <NurseDashboardPage nurseInfo={nurseInfo} onLogout={handleNurseLogout} />
            : <NurseLoginPage onLogin={handleNurseLogin} />
          }
        </div>
      </main>
    </>
  );
}
