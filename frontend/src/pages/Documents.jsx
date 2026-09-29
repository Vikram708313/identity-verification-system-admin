import { useEffect, useMemo, useState } from "react";
import {
  FileCheck,
  Search,
  Eye,
  ShieldCheck,
  X,
  ArrowLeft,
  CalendarDays,
  User,
  Hash,
  CheckCircle2,
} from "lucide-react";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./Documents.css";

export default function Documents() {
  const [documents, setDocuments] = useState([]);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("All");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [selectedDocument, setSelectedDocument] = useState(null);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await api.get("/documents");

      const data = Array.isArray(response.data)
        ? response.data
        : response.data.documents || [];

      setDocuments(data);
    } catch (err) {
      console.error("Failed to load documents:", err);
      setError("Unable to load documents.");
    } finally {
      setLoading(false);
    }
  };

  const documentTypes = useMemo(() => {
    const types = documents
      .map((document) => document.document_type)
      .filter(Boolean);

    return ["All", ...new Set(types)];
  }, [documents]);

  const filteredDocuments = documents.filter((document) => {
    const searchText = search.toLowerCase();

    const type =
      document.document_type?.toLowerCase() || "";

    const number =
      document.document_number?.toLowerCase() || "";

    const personId =
      String(document.person_id ?? "").toLowerCase();

    const matchesSearch =
      type.includes(searchText) ||
      number.includes(searchText) ||
      personId.includes(searchText);

    const matchesFilter =
      filter === "All" ||
      document.document_type === filter;

    return matchesSearch && matchesFilter;
  });

  const openDocument = (document) => {
    setSelectedDocument(document);
  };

  const closeDocument = () => {
    setSelectedDocument(null);
  };

  return (
    <div className="documents-app">

      <Sidebar />

      <main className="documents-main">

        {/* =================================================
            HEADER
        ================================================= */}

        <header className="documents-header">

          <div>

            <p className="documents-eyebrow">
              DOCUMENT MANAGEMENT
            </p>

            <h1>Documents</h1>

            <p>
              Review and manage registered identity documents.
            </p>

          </div>

          <div className="documents-security">

            <ShieldCheck size={18} />

            <span>
              Secure Records
            </span>

          </div>

        </header>


        {/* =================================================
            DOCUMENT COUNT
        ================================================= */}

        <section className="documents-count-card">

          <div className="documents-count-icon">
            <FileCheck size={25} />
          </div>

          <div>

            <span>
              Total Documents
            </span>

            <strong>
              {loading ? "..." : documents.length}
            </strong>

          </div>

        </section>


        {/* =================================================
            DOCUMENT LIST
        ================================================= */}

        <section className="documents-list-card">

          <div className="documents-toolbar">

            <div>

              <h2>
                Registered Documents
              </h2>

              <p>
                {filteredDocuments.length} documents displayed
              </p>

            </div>


            <div className="documents-search">

              <Search size={17} />

              <input
                type="text"
                placeholder="Search document, number or user ID..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />

            </div>

          </div>


          {/* =================================================
              FILTERS
          ================================================= */}

          <div className="document-filters">

            {documentTypes.map((type) => (

              <button
                key={type}
                className={
                  filter === type
                    ? "document-filter active"
                    : "document-filter"
                }
                onClick={() => setFilter(type)}
              >
                {type}
              </button>

            ))}

          </div>


          {/* =================================================
              STATES
          ================================================= */}

          {loading && (
            <div className="documents-message">
              Loading documents...
            </div>
          )}


          {error && (
            <div className="documents-message error">
              {error}
            </div>
          )}


          {!loading &&
            !error &&
            filteredDocuments.length === 0 && (

              <div className="documents-empty">

                <FileCheck size={34} />

                <strong>
                  No documents found
                </strong>

                <span>
                  Try changing your search or document filter.
                </span>

              </div>

            )}


          {/* =================================================
              TABLE
          ================================================= */}

          {!loading &&
            !error &&
            filteredDocuments.length > 0 && (

              <div className="documents-table-wrapper">

                <table className="documents-table">

                  <thead>

                    <tr>
                      <th>Document</th>
                      <th>User ID</th>
                      <th>Document Number</th>
                      <th>Status</th>
                      <th>Action</th>
                    </tr>

                  </thead>


                  <tbody>

                    {filteredDocuments.map(
                      (document, index) => (

                        <tr key={document.id ?? index}>

                          <td>

                            <div className="document-cell">

                              <div className="document-cell-icon">
                                <FileCheck size={18} />
                              </div>

                              <div>

                                <strong>
                                  {document.document_type ||
                                    "Identity Document"}
                                </strong>

                                <span>
                                  Document record
                                </span>

                              </div>

                            </div>

                          </td>


                          <td>

                            <span className="document-user-id">
                              #{document.person_id ?? "N/A"}
                            </span>

                          </td>


                          <td>

                            <span className="document-number">
                              {document.document_number ||
                                "Not available"}
                            </span>

                          </td>


                          <td>

                            <span className="document-status-badge">

                              <CheckCircle2 size={13} />

                              Registered

                            </span>

                          </td>


                          <td>

                            <button
                              className="document-open-button"
                              onClick={() =>
                                openDocument(document)
                              }
                            >
                              <Eye size={15} />
                              View
                            </button>

                          </td>

                        </tr>

                      )
                    )}

                  </tbody>

                </table>

              </div>

            )}

        </section>

      </main>


      {/* =================================================
          DOCUMENT DETAIL
      ================================================= */}

      {selectedDocument && (

        <div className="document-modal-overlay">

          <section className="document-detail-panel">

            {/* HEADER */}

            <header className="document-detail-header">

              <button
                className="document-back-button"
                onClick={closeDocument}
              >
                <ArrowLeft size={18} />
              </button>


              <div>

                <p>
                  DOCUMENT DETAILS
                </p>

                <h2>
                  {selectedDocument.document_type ||
                    "Identity Document"}
                </h2>

              </div>


              <button
                className="document-close-button"
                onClick={closeDocument}
              >
                <X size={20} />
              </button>

            </header>


            {/* BODY */}

            <div className="document-detail-body">

              {/* DOCUMENT PREVIEW */}

              <div className="document-preview-card">

                <div className="document-preview-header">
                  TRUSTVISION
                </div>


                <div className="document-preview-content">

                  <div className="document-preview-icon">
                    <FileCheck size={45} />
                  </div>

                  <h3>
                    {selectedDocument.document_type ||
                      "Identity Document"}
                  </h3>

                  <span>
                    Document Preview
                  </span>

                  <div className="preview-lines">
                    <div />
                    <div />
                    <div className="short" />
                  </div>

                </div>

              </div>


              {/* DOCUMENT INFO */}

              <div className="document-info-card">

                <div className="document-info-title">

                  <div>

                    <p>
                      INFORMATION
                    </p>

                    <h3>
                      Document Information
                    </h3>

                  </div>

                  <ShieldCheck size={20} />

                </div>


                <InfoRow
                  icon={<FileCheck size={16} />}
                  label="Document name"
                  value={
                    selectedDocument.document_type ||
                    "Identity Document"
                  }
                />


                <InfoRow
                  icon={<Hash size={16} />}
                  label="Document number"
                  value={
                    selectedDocument.document_number ||
                    "Not available"
                  }
                />


                <InfoRow
                  icon={<User size={16} />}
                  label="User ID"
                  value={
                    `#${selectedDocument.person_id ?? "N/A"}`
                  }
                />


                <InfoRow
                  icon={<CalendarDays size={16} />}
                  label="Uploaded"
                  value={
                    formatDate(
                      selectedDocument.created_at
                    )
                  }
                />


                <InfoRow
                  icon={<CalendarDays size={16} />}
                  label="Last updated"
                  value={
                    selectedDocument.updated_at
                      ? formatDate(
                          selectedDocument.updated_at
                        )
                      : selectedDocument.created_at
                      ? formatDate(
                          selectedDocument.created_at
                        )
                      : "Not available"
                  }
                />


                <div className="document-verified-box">

                  <CheckCircle2 size={19} />

                  <div>

                    <strong>
                      Document registered
                    </strong>

                    <span>
                      This document is currently associated
                      with the selected identity.
                    </span>

                  </div>

                </div>

              </div>

            </div>

          </section>

        </div>

      )}

    </div>
  );
}


/* =========================================================
   INFORMATION ROW
   ========================================================= */

function InfoRow({ icon, label, value }) {
  return (
    <div className="document-info-row">

      <div className="document-info-label">

        {icon}

        <span>
          {label}
        </span>

      </div>

      <strong>
        {value}
      </strong>

    </div>
  );
}


/* =========================================================
   DATE FORMAT
   ========================================================= */

function formatDate(value) {
  if (!value) {
    return "Not available";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}