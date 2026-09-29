import { useEffect, useState } from "react";
import {
  Users,
  Search,
  Eye,
  ShieldCheck,
  FileCheck,
  X,
  ArrowLeft,
} from "lucide-react";

import api from "../services/api";
import Sidebar from "../components/Sidebar";

import "./People.css";

export default function People() {
  const [people, setPeople] = useState([]);
  const [documents, setDocuments] = useState([]);

  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [documentLoading, setDocumentLoading] = useState(false);

  const [error, setError] = useState("");

  const [selectedPerson, setSelectedPerson] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);

  useEffect(() => {
    loadPeople();
    loadDocuments();
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
      setError("Unable to load people data.");
    } finally {
      setLoading(false);
    }
  };

  const loadDocuments = async () => {
    setDocumentLoading(true);

    try {
      const response = await api.get("/documents");

      const data = Array.isArray(response.data)
        ? response.data
        : response.data.documents || [];

      setDocuments(data);
    } catch (err) {
      console.error("Failed to load documents:", err);
    } finally {
      setDocumentLoading(false);
    }
  };

  const getPersonName = (person) => {
    return (
      person.name ||
      person.full_name ||
      person.username ||
      `Person ${person.id ?? ""}`
    );
  };

  const getPersonDocuments = (person) => {
    if (!person) {
      return [];
    }

    return documents.filter((document) => {
      return (
        String(document.person_id ?? "") ===
        String(person.id ?? "")
      );
    });
  };

  const filteredPeople = people.filter((person) => {
    const searchText = search.toLowerCase();

    const name = getPersonName(person).toLowerCase();

    const id = String(person.id ?? "").toLowerCase();

    return (
      name.includes(searchText) ||
      id.includes(searchText)
    );
  });

  const openPerson = (person) => {
    setSelectedPerson(person);
    setSelectedDocument(null);
  };

  const closePerson = () => {
    setSelectedPerson(null);
    setSelectedDocument(null);
  };

  const openDocument = (document) => {
    setSelectedDocument(document);
  };

  const closeDocument = () => {
    setSelectedDocument(null);
  };

  return (
    <div className="app-layout">

      <Sidebar />

      <main className="people-main">

        {/* =================================================
            HEADER
        ================================================= */}

        <header className="people-header">

          <div>

            <p className="people-eyebrow">
              IDENTITY DATABASE
            </p>

            <h1>People</h1>

            <p>
              View registered identities and their documents.
            </p>

          </div>

          <div className="people-security">

            <ShieldCheck size={19} />

            <span>
              System Secure
            </span>

          </div>

        </header>


        {/* =================================================
            REGISTERED PEOPLE COUNT
        ================================================= */}

        <section className="registered-count-card">

          <div className="registered-count-icon">
            <Users size={25} />
          </div>

          <div>

            <span>
              Registered People
            </span>

            <strong>
              {loading ? "..." : people.length}
            </strong>

          </div>

        </section>


        {/* =================================================
            PEOPLE LIST
        ================================================= */}

        <section className="people-list-card">

          <div className="people-list-header">

            <div>

              <h2>
                Registered People
              </h2>

              <p>
                {filteredPeople.length} identities displayed
              </p>

            </div>


            <div className="people-search">

              <Search size={17} />

              <input
                type="text"
                placeholder="Search name or ID..."
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
              />

            </div>

          </div>


          {loading && (
            <div className="people-empty">
              Loading registered people...
            </div>
          )}


          {error && (
            <div className="people-error">
              {error}
            </div>
          )}


          {!loading &&
            !error &&
            filteredPeople.length === 0 && (
              <div className="people-empty">
                No people found.
              </div>
            )}


          {!loading &&
            !error &&
            filteredPeople.length > 0 && (

              <div className="people-table-wrapper">

                <table className="people-modern-table">

                  <thead>

                    <tr>
                      <th>User ID</th>
                      <th>Person</th>
                      <th>Documents</th>
                      <th>Action</th>
                    </tr>

                  </thead>


                  <tbody>

                    {filteredPeople.map((person, index) => {

                      const personDocuments =
                        getPersonDocuments(person);

                      const name =
                        getPersonName(person);

                      return (

                        <tr key={person.id ?? index}>

                          <td>

                            <span className="user-id">
                              #{person.id ?? "N/A"}
                            </span>

                          </td>


                          <td>

                            <div className="person-cell">

                              <div className="person-avatar">
                                {name.charAt(0).toUpperCase()}
                              </div>

                              <div>

                                <strong>
                                  {name}
                                </strong>

                                <span>
                                  Identity record
                                </span>

                              </div>

                            </div>

                          </td>


                          <td>

                            <div className="document-count">

                              <FileCheck size={16} />

                              <span>
                                {personDocuments.length}
                              </span>

                              <small>
                                {personDocuments.length === 1
                                  ? "document"
                                  : "documents"}
                              </small>

                            </div>

                          </td>


                          <td>

                            <button
                              className="person-view-button"
                              onClick={() =>
                                openPerson(person)
                              }
                            >
                              <Eye size={16} />
                              View
                            </button>

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


      {/* =================================================
          PERSON DOCUMENT DRAWER
      ================================================= */}

      {selectedPerson && !selectedDocument && (

        <div className="people-modal-overlay">

          <section className="person-detail-panel">

            <div className="person-detail-header">

              <button
                className="detail-back-button"
                onClick={closePerson}
              >
                <ArrowLeft size={18} />
              </button>

              <div>

                <p>
                  USER PROFILE
                </p>

                <h2>
                  {getPersonName(selectedPerson)}
                </h2>

                <span>
                  User ID #{selectedPerson.id ?? "N/A"}
                </span>

              </div>

              <button
                className="detail-close-button"
                onClick={closePerson}
              >
                <X size={20} />
              </button>

            </div>


            <div className="person-detail-body">

              <div className="person-profile-card">

                <div className="large-person-avatar">
                  {getPersonName(selectedPerson)
                    .charAt(0)
                    .toUpperCase()}
                </div>

                <div>

                  <strong>
                    {getPersonName(selectedPerson)}
                  </strong>

                  <span>
                    Registered identity
                  </span>

                </div>

                <ShieldCheck size={21} />

              </div>


              <div className="document-section-header">

                <div>

                  <p>
                    IDENTITY DOCUMENTS
                  </p>

                  <h3>
                    Documents
                  </h3>

                </div>

                <span>
                  {getPersonDocuments(selectedPerson).length}
                </span>

              </div>


              {documentLoading && (
                <div className="document-list-empty">
                  Loading documents...
                </div>
              )}


              {!documentLoading &&
                getPersonDocuments(selectedPerson).length === 0 && (

                  <div className="document-list-empty">

                    <FileCheck size={28} />

                    <strong>
                      No documents found
                    </strong>

                    <span>
                      No documents are currently registered
                      for this person.
                    </span>

                  </div>

                )}


              {!documentLoading &&
                getPersonDocuments(selectedPerson).map(
                  (document) => (

                    <div
                      className="person-document-row"
                      key={document.id}
                    >

                      <div className="person-document-icon">
                        <FileCheck size={21} />
                      </div>

                      <div className="person-document-info">

                        <strong>
                          {document.document_type ||
                            "Identity Document"}
                        </strong>

                        <span>
                          {document.document_number ||
                            "Document number unavailable"}
                        </span>

                        <small>
                          {document.created_at
                            ? `Uploaded ${formatDate(
                                document.created_at
                              )}`
                            : "Upload date unavailable"}
                        </small>

                      </div>


                      <button
                        className="document-view-button"
                        onClick={() =>
                          openDocument(document)
                        }
                      >
                        <Eye size={16} />
                        View
                      </button>

                    </div>

                  )
                )}

            </div>

          </section>

        </div>

      )}


      {/* =================================================
          DOCUMENT VIEWER
      ================================================= */}

      {selectedDocument && (

        <div className="people-modal-overlay">

          <section className="document-viewer-panel">

            <header className="document-viewer-header">

              <button
                className="detail-back-button"
                onClick={closeDocument}
              >
                <ArrowLeft size={18} />
              </button>

              <div>

                <p>
                  DOCUMENT VIEWER
                </p>

                <h2>
                  {selectedDocument.document_type ||
                    "Identity Document"}
                </h2>

              </div>

              <button
                className="detail-close-button"
                onClick={closeDocument}
              >
                <X size={20} />
              </button>

            </header>


            <div className="document-viewer-body">

              <div className="document-preview">

                <div className="document-preview-top">
                  TRUSTVISION
                </div>

                <div className="document-preview-icon">
                  <FileCheck size={48} />
                </div>

                <h3>
                  {selectedDocument.document_type ||
                    "Identity Document"}
                </h3>

                <p>
                  Document preview
                </p>

                <div className="document-preview-line" />
                <div className="document-preview-line short" />
                <div className="document-preview-line" />

              </div>


              <div className="document-information">

                <div className="document-info-heading">

                  <p>
                    DOCUMENT INFORMATION
                  </p>

                  <ShieldCheck size={20} />

                </div>


                <div className="document-info-row">

                  <span>
                    Document name
                  </span>

                  <strong>
                    {selectedDocument.document_type ||
                      "Identity Document"}
                  </strong>

                </div>


                <div className="document-info-row">

                  <span>
                    Document number
                  </span>

                  <strong>
                    {selectedDocument.document_number ||
                      "Not available"}
                  </strong>

                </div>


                <div className="document-info-row">

                  <span>
                    Person ID
                  </span>

                  <strong>
                    #{selectedDocument.person_id ??
                      "N/A"}
                  </strong>

                </div>


                <div className="document-info-row">

                  <span>
                    Uploaded
                  </span>

                  <strong>
                    {selectedDocument.created_at
                      ? formatDate(
                          selectedDocument.created_at
                        )
                      : "Not available"}
                  </strong>

                </div>


                <div className="document-info-row">

                  <span>
                    Last updated
                  </span>

                  <strong>
                    {selectedDocument.updated_at
                      ? formatDate(
                          selectedDocument.updated_at
                        )
                      : selectedDocument.created_at
                      ? formatDate(
                          selectedDocument.created_at
                        )
                      : "Not available"}
                  </strong>

                </div>


                <div className="document-status">

                  <ShieldCheck size={18} />

                  <div>

                    <strong>
                      Document registered
                    </strong>

                    <span>
                      This document is associated with
                      the selected identity.
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