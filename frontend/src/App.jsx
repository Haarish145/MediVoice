import { useState } from "react";
import PatientPage from "./pages/PatientPage";
import NurseLoginPage from "./pages/NurseLoginPage";
import NurseDashboardPage from "./pages/NurseDashboardPage";
import "./index.css";

export default function App() {
  const [activeTab, setActiveTab] = useState("patient"); // patient | nurse
  const [nurseInfo, setNurseInfo] = useState(null);

  const handleNurseLogin  = (data) => setNurseInfo(data);
  const handleNurseLogout = ()     => setNurseInfo(null);

  return (
    <>
      <header className="app-header">
        {/* Brand */}
        <div className="brand-title">
          <span className="brand-icon">🏥</span>
          MediVoice
          <span className="team-badge">Team MediVoice</span>
        </div>

        {/* Navigation */}
        <nav className="nav-tabs" aria-label="Main navigation">
          <button
            id="tab-patient"
            className={`nav-tab ${activeTab === "patient" ? "active" : ""}`}
            onClick={() => setActiveTab("patient")}
            aria-selected={activeTab === "patient"}
          >
            {/* Short label on very small screens */}
            <span className="tab-label-full">👤 Patient Intake</span>
            <span className="tab-label-short">👤 Patient</span>
          </button>
          <button
            id="tab-nurse"
            className={`nav-tab ${activeTab === "nurse" ? "active" : ""}`}
            onClick={() => setActiveTab("nurse")}
            aria-selected={activeTab === "nurse"}
          >
            <span className="tab-label-full">🩺 Nurse Dashboard</span>
            <span className="tab-label-short">🩺 Nurse</span>
          </button>
        </nav>
      </header>

      <main>
        <div
          className="patient-view-container"
          style={{ display: activeTab === "patient" ? "block" : "none" }}
        >
          <PatientPage />
        </div>
        <div
          className="nurse-view-container"
          style={{ display: activeTab === "nurse" ? "block" : "none" }}
        >
          {nurseInfo
            ? <NurseDashboardPage nurseInfo={nurseInfo} onLogout={handleNurseLogout} />
            : <div style={{ padding: "2rem 0.75rem" }}><NurseLoginPage onLogin={handleNurseLogin} /></div>
          }
        </div>
      </main>
    </>
  );
}
