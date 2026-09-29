import { useEffect, useState } from "react";
import {
  Users,
  CheckCircle2,
  Clock3,
  ShieldCheck,
  ScanFace,
  ChevronRight,
  FileCheck,
} from "lucide-react";

import api from "../services/api";
import Sidebar from "../components/Sidebar";
import "./Dashboard.css";

export default function Dashboard() {
  const [people, setPeople] = useState([]);
  const [history, setHistory] = useState([]);

  const [loadingPeople, setLoadingPeople] = useState(true);
  const [loadingHistory, setLoadingHistory] = useState(true);

  const [peopleError, setPeopleError] = useState("");
  const [historyError, setHistoryError] = useState("");

  useEffect(() => {
    loadPeople();
    loadHistory();
  }, []);

  const loadPeople = async () => {
    try {
      const response = await api.get("/people");

      const data = Array.isArray(response.data)
        ? response.data
        : response.data.people || [];

      setPeople(data);
    } catch (err) {
      console.error("Failed to load people:", err);
      setPeopleError("Unable to load people data.");
    } finally {
      setLoadingPeople(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await api.get("/verification/history");

      const data = Array.isArray(response.data)
        ? response.data
        : response.data.history || [];

      setHistory(data);
    } catch (err) {
      console.error("Failed to load verification history:", err);
      setHistoryError("Unable to load verification history.");
    } finally {
      setLoadingHistory(false);
    }
  };

  const isToday = (dateValue) => {
    if (!dateValue) return false;

    const date = new Date(dateValue);
    const today = new Date();

    return (
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate()
    );
  };

  const documentsVerifiedToday = history.filter(
    (item) =>
      item.verification_method === "document" &&
      item.status === "COMPLETED" &&
      isToday(item.created_at)
  ).length;

  const formatMethod = (method) => {
    if (!method) return "—";

    if (method === "document") return "Document";
    if (method === "qr") return "QR";

    return method;
  };

  const formatDate = (dateValue) => {
    if (!dateValue) return "—";

    const date = new Date(dateValue);

    return date.toLocaleString([], {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="dashboard-shell">
      <Sidebar />

      <main className="dashboard-main">

        {/* ================= HEADER ================= */}

        <header className="dashboard-topbar">

          <div>
            <p className="dashboard-eyebrow">
              TRUSTVISION ADMINISTRATION
            </p>

            <h1>Dashboard</h1>

            <p className="dashboard-subtitle">
              Manage identity verification and review verification activity.
            </p>
          </div>

          <div className="admin-block">

            <div className="admin-block-avatar">
              A
            </div>

            <div className="admin-block-info">
              <strong>Administrator</strong>
              <span>System Admin</span>
            </div>

            <ShieldCheck size={21} />

          </div>

        </header>


        {/* ================= VERIFY IDENTITY ================= */}

        <section className="verification-section">

          <div className="section-heading">

            <div>
              <p className="section-eyebrow">
                VERIFICATION CENTER
              </p>

              <h2>Verify an identity</h2>

              <p>
                Start a secure identity verification using face,
                document, or QR verification.
              </p>
            </div>

          </div>


          <div className="mandatory-face-card">

            <div className="mandatory-face-icon">
              <ScanFace size={28} />
            </div>

            <div className="mandatory-face-content">

              <div className="mandatory-face-title">

                <h3>Face verification required</h3>

                <span className="required-badge">
                  Required
                </span>

              </div>

              <p>
                The person's face must be verified before document
                verification or QR scanning can continue.
              </p>

            </div>

            <a
              href="/verification"
              className="start-verification-button"
            >
              Start Verification
              <ChevronRight size={18} />
            </a>

          </div>

        </section>


        {/* ================= STATISTICS ================= */}

        <section className="dashboard-stats">

          <div className="dashboard-stat">

            <div className="dashboard-stat-icon">
              <Users size={21} />
            </div>

            <div>
              <span>Registered People</span>

              <strong>
                {loadingPeople ? "..." : people.length}
              </strong>
            </div>

          </div>


          <div className="dashboard-stat">

            <div className="dashboard-stat-icon">
              <CheckCircle2 size={21} />
            </div>

            <div>
              <span>Documents Verified Today</span>

              <strong>
                {loadingHistory ? "..." : documentsVerifiedToday}
              </strong>
            </div>

          </div>

        </section>


        {/* ================= VERIFICATION HISTORY ================= */}

        <section className="history-card">

          <div className="history-header">

            <div>

              <p className="section-eyebrow">
                AUDIT ACTIVITY
              </p>

              <h2>Verification History</h2>

              <p>
                Recent identity verification attempts.
              </p>

            </div>

            <div className="history-header-icon">
              <Clock3 size={21} />
            </div>

          </div>


          {peopleError && (
            <div className="dashboard-error">
              {peopleError}
            </div>
          )}

          {historyError && (
            <div className="dashboard-error">
              {historyError}
            </div>
          )}


          <div className="history-table">

            <div className="history-table-header">
              <span>User ID</span>
              <span>Name</span>
              <span>Method</span>
              <span>Status</span>
              <span>Date</span>
            </div>


            {loadingHistory ? (

              <div className="history-empty">

                <div className="history-empty-icon">
                  <Clock3 size={24} />
                </div>

                <div>
                  <strong>
                    Loading verification history...
                  </strong>

                  <span>
                    Retrieving recent verification records.
                  </span>
                </div>

              </div>

            ) : history.length === 0 ? (

              <div className="history-empty">

                <div className="history-empty-icon">
                  <Clock3 size={24} />
                </div>

                <div>
                  <strong>
                    No verification history yet
                  </strong>

                  <span>
                    Completed identity verification attempts will appear here.
                  </span>
                </div>

              </div>

            ) : (

              <div className="history-table-body">

                {history.map((record) => (

                  <div
                    className="history-row"
                    key={record.id}
                  >

                    <span className="history-user-id">
                      #{String(record.person_id).padStart(3, "0")}
                    </span>

                    <span className="history-name">
                      {record.full_name || "Unknown"}
                    </span>

                    <span className="history-method">

                      {record.verification_method === "document" ? (
                        <FileCheck size={15} />
                      ) : (
                        <ScanFace size={15} />
                      )}

                      {formatMethod(record.verification_method)}

                    </span>

                    <span
                      className={`history-status ${
                        record.status === "COMPLETED"
                          ? "completed"
                          : "pending"
                      }`}
                    >
                      <CheckCircle2 size={14} />

                      {record.status || "PENDING"}

                    </span>

                    <span className="history-date">
                      {formatDate(record.created_at)}
                    </span>

                  </div>

                ))}

              </div>

            )}

          </div>

        </section>

      </main>
    </div>
  );
}