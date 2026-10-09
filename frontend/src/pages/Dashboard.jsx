
import { useEffect, useState } from "react";
import {
  Users,
  CheckCircle2,
  Clock3,
  ShieldCheck,
  ScanFace,
  ChevronRight,
  FileCheck,
  ArrowRight,
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

      const sorted = [...data].sort(
        (a, b) =>
          new Date(b.created_at || 0).getTime() -
          new Date(a.created_at || 0).getTime()
      );

      setHistory(sorted);
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
      item.verification_method?.toLowerCase() === "document" &&
      ["COMPLETED", "APPROVED"].includes(
        (item.status || "").toUpperCase()
      ) &&
      isToday(item.created_at)
  ).length;

  const formatMethod = (method) => {
    if (!method) return "—";

    const value = method.toLowerCase();

    if (value === "document") return "Document";
    if (value === "qr") return "QR";
    if (value === "face") return "Face";

    return method;
  };

  const formatStatus = (status) => {
    if (!status) return "Pending";

    const value = status.toUpperCase();

    if (value === "COMPLETED" || value === "APPROVED") {
      return "Approved";
    }

    if (value === "PENDING" || value === "IN_REVIEW") {
      return "Pending";
    }

    if (value === "REQUEST" || value === "REQUESTED") {
      return "Request";
    }

    return status.replaceAll("_", " ");
  };

  const getStatusClass = (status) => {
    const value = (status || "PENDING").toUpperCase();

    if (["COMPLETED", "APPROVED"].includes(value)) {
      return "completed";
    }

    if (["REJECTED", "FAILED"].includes(value)) {
      return "rejected";
    }

    return "pending";
  };

  const formatDate = (dateValue) => {
    if (!dateValue) return "—";

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) return "—";

    return date.toLocaleString([], {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const recentHistory = history.slice(0, 5);

  return (
    <div className="dashboard-shell">
      <Sidebar />

      <main className="dashboard-main">
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
            <div className="admin-block-avatar">A</div>

            <div className="admin-block-info">
              <strong>Administrator</strong>
              <span>System Admin</span>
            </div>

            <ShieldCheck size={21} />
          </div>
        </header>

        <section className="verification-section">
          <div className="section-heading">
            <div>
              <p className="section-eyebrow">VERIFICATION CENTER</p>
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
                <span className="required-badge">Required</span>
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

        <section className="dashboard-stats">
          <div className="dashboard-stat">
            <div className="dashboard-stat-icon">
              <Users size={21} />
            </div>

            <div>
              <span>Registered People</span>
              <strong>{loadingPeople ? "..." : people.length}</strong>
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

        <section className="history-card">
          <div className="history-header">
            <div>
              <p className="section-eyebrow">AUDIT ACTIVITY</p>
              <h2>Verification History</h2>

              <p>
                Showing the five most recent verification records.
              </p>
            </div>

            <div className="history-header-icon">
              <Clock3 size={21} />
            </div>
          </div>

          {peopleError && (
            <div className="dashboard-error">{peopleError}</div>
          )}

          {historyError && (
            <div className="dashboard-error">{historyError}</div>
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
                  <strong>Loading verification history...</strong>
                  <span>Retrieving recent verification records.</span>
                </div>
              </div>
            ) : recentHistory.length === 0 ? (
              <div className="history-empty">
                <div className="history-empty-icon">
                  <Clock3 size={24} />
                </div>

                <div>
                  <strong>No verification history yet</strong>
                  <span>
                    Verification attempts will appear here when available.
                  </span>
                </div>
              </div>
            ) : (
              <div className="history-table-body">
                {recentHistory.map((record) => (
                  <div className="history-row" key={record.id}>
                    <span className="history-user-id">
                      #{String(record.person_id ?? "—").padStart(3, "0")}
                    </span>

                    <span className="history-name">
                      {record.full_name || "Unknown"}
                    </span>

                    <span className="history-method">
                      {record.verification_method?.toLowerCase() ===
                      "document" ? (
                        <FileCheck size={15} />
                      ) : (
                        <ScanFace size={15} />
                      )}

                      {formatMethod(record.verification_method)}
                    </span>

                    <span
                      className={`history-status ${getStatusClass(
                        record.status
                      )}`}
                    >
                      <CheckCircle2 size={14} />
                      {formatStatus(record.status)}
                    </span>

                    <span className="history-date">
                      {formatDate(record.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="history-footer">
            <a href="/verification-history" className="history-all-button">
              All
              <ArrowRight size={16} />
            </a>
          </div>
        </section>
      </main>
    </div>
  );
}