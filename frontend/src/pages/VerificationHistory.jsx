
import { useEffect, useMemo, useState } from "react";
import {
  History,
  Search,
  ShieldCheck,
  CalendarDays,
  User,
  CheckCircle2,
  Clock3,
  ClipboardList,
  RefreshCw,
} from "lucide-react";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./Documents.css";

export default function VerificationHistory() {
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/verification/history");

      const data = Array.isArray(response.data)
        ? response.data
        : response.data.history || [];

      setHistory(data);
    } catch (err) {
      console.error("Failed to load verification history:", err);
      setError("Unable to load verification history.");
    } finally {
      setLoading(false);
    }
  };

  const getStatus = (item) => {
    const status = String(item.status || "").toUpperCase();

    if (
      ["COMPLETED", "APPROVED", "SUCCESS", "VERIFIED"].includes(status)
    ) {
      return "Approved";
    }

    if (
      ["REQUEST", "REQUESTED"].includes(status)
    ) {
      return "Request";
    }

    if (
      ["PENDING", "IN_REVIEW", "PROCESSING"].includes(status)
    ) {
      return "Pending";
    }

    return item.status || "Pending";
  };

  const sortedHistory = useMemo(() => {
    return [...history].sort((a, b) => {
      const dateA = new Date(
        a.created_at || a.date || a.timestamp || 0
      ).getTime();

      const dateB = new Date(
        b.created_at || b.date || b.timestamp || 0
      ).getTime();

      return dateB - dateA;
    });
  }, [history]);

  const filteredHistory = sortedHistory.filter((item) => {
    const userId = String(
      item.person_id ?? item.user_id ?? item.person?.id ?? ""
    ).toLowerCase();

    const dateValue =
      item.created_at || item.date || item.timestamp || "";

    const dateText = formatDate(dateValue).toLowerCase();
    const rawDate = String(dateValue).toLowerCase();

    const matchesSearch =
      userId.includes(search.toLowerCase()) ||
      dateText.includes(search.toLowerCase()) ||
      rawDate.includes(search.toLowerCase());

    const matchesFilter =
      filter === "All" || getStatus(item) === filter;

    return matchesSearch && matchesFilter;
  });

  const counts = {
    All: history.length,
    Approved: history.filter(
      (item) => getStatus(item) === "Approved"
    ).length,
    Pending: history.filter(
      (item) => getStatus(item) === "Pending"
    ).length,
    Request: history.filter(
      (item) => getStatus(item) === "Request"
    ).length,
  };

  return (
    <div className="documents-app">
      <Sidebar />

      <main className="documents-main">
        <header className="documents-header">
          <div>
            <p className="documents-eyebrow">
              VERIFICATION MANAGEMENT
            </p>

            <h1>Verification History</h1>

            <p>
              Search and review previous identity verification records.
            </p>
          </div>

          <div className="documents-security">
            <ShieldCheck size={18} />
            <span>Secure Records</span>
          </div>
        </header>

        <section className="documents-count-card">
          <div className="documents-count-icon">
            <History size={25} />
          </div>

          <div>
            <span>Total Verifications</span>
            <strong>{loading ? "..." : history.length}</strong>
          </div>
        </section>

        <section className="documents-list-card">
          <div className="documents-toolbar">
            <div>
              <h2>All Verification Records</h2>
              <p>
                {filteredHistory.length} records displayed
              </p>
            </div>

            <div className="documents-search">
              <Search size={17} />

              <input
                type="text"
                placeholder="Search user ID or date..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />

              <button
                type="button"
                title="Refresh history"
                onClick={loadHistory}
                disabled={loading}
                style={{
                  border: "none",
                  background: "transparent",
                  cursor: loading ? "default" : "pointer",
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <RefreshCw size={16} />
              </button>
            </div>
          </div>

          <div className="document-filters">
            {["All", "Approved", "Pending", "Request"].map((status) => (
              <button
                key={status}
                className={
                  filter === status
                    ? "document-filter active"
                    : "document-filter"
                }
                onClick={() => setFilter(status)}
              >
                {status} ({counts[status]})
              </button>
            ))}
          </div>

          {loading && (
            <div className="documents-message">
              Loading verification history...
            </div>
          )}

          {error && (
            <div className="documents-message error">
              {error}
            </div>
          )}

          {!loading && !error && filteredHistory.length === 0 && (
            <div className="documents-empty">
              <History size={34} />

              <strong>No verification records found</strong>

              <span>
                Try changing your search or status filter.
              </span>
            </div>
          )}

          {!loading && !error && filteredHistory.length > 0 && (
            <div className="documents-table-wrapper">
              <table className="documents-table">
                <thead>
                  <tr>
                    <th>User ID</th>
                    <th>Verification Method</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredHistory.map((item, index) => {
                    const status = getStatus(item);

                    const userId =
                      item.person_id ??
                      item.user_id ??
                      item.person?.id ??
                      "N/A";

                    const method =
                      item.method ||
                      item.verification_method ||
                      item.type ||
                      "Identity Verification";

                    const date =
                      item.created_at ||
                      item.date ||
                      item.timestamp;

                    return (
                      <tr key={item.id ?? index}>
                        <td>
                          <div className="document-cell">
                            <div className="document-cell-icon">
                              <User size={18} />
                            </div>

                            <div>
                              <strong>#{userId}</strong>
                              <span>User ID</span>
                            </div>
                          </div>
                        </td>

                        <td>
                          <span className="document-number">
                            {method}
                          </span>
                        </td>

                        <td>
                          <span
                            className={`verification-history-status ${
                              status.toLowerCase()
                            }`}
                          >
                            {status === "Approved" && (
                              <CheckCircle2 size={13} />
                            )}

                            {status === "Pending" && (
                              <Clock3 size={13} />
                            )}

                            {status === "Request" && (
                              <ClipboardList size={13} />
                            )}

                            {status}
                          </span>
                        </td>

                        <td>
                          <span className="document-number">
                            <CalendarDays
                              size={14}
                              style={{
                                display: "inline",
                                verticalAlign: "middle",
                                marginRight: 6,
                              }}
                            />
                            {formatDate(date)}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}