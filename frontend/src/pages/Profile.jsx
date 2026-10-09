import { useEffect, useState } from "react";

import {
  UserCircle,
  Settings,
  ShieldCheck,
  LogOut,
  Mail,
  Hash,
  Shield,
  FileText,
  LockKeyhole,
  ScrollText,
  ChevronRight,
  Type,
  Languages,
} from "lucide-react";

import { useNavigate } from "react-router-dom";

import api from "../services/api";

import "./Profile.css";


export default function Profile() {
  const navigate = useNavigate();

  const [admin, setAdmin] = useState(null);
  const [loadingAdmin, setLoadingAdmin] = useState(true);

  const [activeTab, setActiveTab] = useState("account");

  const [font, setFont] = useState(
    localStorage.getItem("font") || "system"
  );

  const [language, setLanguage] = useState(
    localStorage.getItem("language") || "english"
  );


  // LOAD ADMIN PROFILE
  useEffect(() => {
    const loadAdminProfile = async () => {
      try {
        const response = await api.get("/auth/me");

        setAdmin(response.data);
      } catch (error) {
        console.error(
          "Failed to load admin profile:",
          error
        );
      } finally {
        setLoadingAdmin(false);
      }
    };

    loadAdminProfile();
  }, []);


  // SAVE FONT
  useEffect(() => {
    localStorage.setItem("font", font);
  }, [font]);


  // SAVE LANGUAGE
  useEffect(() => {
    localStorage.setItem("language", language);
  }, [language]);


  // LOGOUT
  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("role");

    navigate("/");
  };


  return (
    <main className="profile-main">

      {/* HEADER */}

      <div className="profile-header">

        <div className="profile-header-icon">
          <UserCircle size={28} />
        </div>

        <div>
          <h1>Profile</h1>

          <p>
            Manage your account, application settings and information.
          </p>
        </div>

      </div>


      {/* PROFILE NAVIGATION */}

      <div className="profile-layout">

        <aside className="profile-tabs">

          {/* ACCOUNT */}

          <button
            className={`profile-tab ${
              activeTab === "account" ? "active" : ""
            }`}
            onClick={() => setActiveTab("account")}
          >
            <UserCircle size={19} />

            <div>
              <strong>Account</strong>
              <span>Admin information</span>
            </div>

            <ChevronRight size={17} />
          </button>


          {/* SETTINGS */}

          <button
            className={`profile-tab ${
              activeTab === "settings" ? "active" : ""
            }`}
            onClick={() => setActiveTab("settings")}
          >
            <Settings size={19} />

            <div>
              <strong>Settings</strong>
              <span>App preferences</span>
            </div>

            <ChevronRight size={17} />
          </button>


          {/* ABOUT */}

          <button
            className={`profile-tab ${
              activeTab === "about" ? "active" : ""
            }`}
            onClick={() => setActiveTab("about")}
          >
            <ShieldCheck size={19} />

            <div>
              <strong>About Us</strong>
              <span>TrustVision information</span>
            </div>

            <ChevronRight size={17} />
          </button>


          {/* LOGOUT */}

          <button
            className="profile-tab logout-tab"
            onClick={handleLogout}
          >
            <LogOut size={19} />

            <div>
              <strong>Log out</strong>
              <span>End current session</span>
            </div>

            <ChevronRight size={17} />
          </button>

        </aside>


        {/* CONTENT */}

        <section className="profile-content">


          {/* ACCOUNT */}

          {activeTab === "account" && (
            <div>

              <div className="profile-section-heading">

                <h2>Account</h2>

                <p>
                  Information associated with the administrator account.
                </p>

              </div>


              <div className="admin-profile-card">

                <div className="admin-avatar">
                  <UserCircle size={42} />
                </div>

                <div>

                  <h3>
                    {loadingAdmin
                      ? "Loading..."
                      : admin?.username || "Administrator"}
                  </h3>

                  <span>
                    {admin?.role || "Administrator"}
                  </span>

                </div>

              </div>


              <div className="account-info-grid">

                <div className="account-info-card">

                  <div className="account-info-icon">
                    <Hash size={18} />
                  </div>

                  <div>

                    <span>Admin No.</span>

                    <strong>
                      {loadingAdmin
                        ? "Loading..."
                        : admin?.id
                          ? `ADM-${String(admin.id).padStart(3, "0")}`
                          : "Not available"}
                    </strong>

                  </div>

                </div>


                <div className="account-info-card">

                  <div className="account-info-icon">
                    <Mail size={18} />
                  </div>

                  <div>

                    <span>Email</span>

                    <strong>
                      {loadingAdmin
                        ? "Loading..."
                        : admin?.email || "Not configured"}
                    </strong>

                  </div>

                </div>


                <div className="account-info-card">

                  <div className="account-info-icon">
                    <Shield size={18} />
                  </div>

                  <div>

                    <span>Role</span>

                    <strong>
                      {loadingAdmin
                        ? "Loading..."
                        : admin?.role || "Not available"}
                    </strong>

                  </div>

                </div>


                <div className="account-info-card">

                  <div className="account-info-icon">
                    <LockKeyhole size={18} />
                  </div>

                  <div>

                    <span>Authentication</span>

                    <strong>
                      Password protected
                    </strong>

                  </div>

                </div>

              </div>

            </div>
          )}


          {/* SETTINGS */}

          {activeTab === "settings" && (
            <div>

              <div className="profile-section-heading">

                <h2>Settings</h2>

                <p>
                  Customize your TrustVision preferences.
                </p>

              </div>


              {/* FONT */}

              <div className="settings-card">

                <div className="settings-card-header">

                  <div className="settings-card-icon">
                    <Type size={19} />
                  </div>

                  <div>

                    <h3>Font</h3>

                    <p>
                      Select the application font style.
                    </p>

                  </div>

                </div>


                <div className="setting-select-wrapper">

                  <select
                    value={font}
                    onChange={(e) =>
                      setFont(e.target.value)
                    }
                  >

                    <option value="system">
                      System Default
                    </option>

                    <option value="inter">
                      Inter
                    </option>

                    <option value="serif">
                      Serif
                    </option>

                  </select>

                </div>

              </div>


              {/* LANGUAGE */}

              <div className="settings-card">

                <div className="settings-card-header">

                  <div className="settings-card-icon">
                    <Languages size={19} />
                  </div>

                  <div>

                    <h3>Language</h3>

                    <p>
                      Select your preferred application language.
                    </p>

                  </div>

                </div>


                <div className="setting-select-wrapper">

                  <select
                    value={language}
                    onChange={(e) =>
                      setLanguage(e.target.value)
                    }
                  >

                    <option value="english">
                      English
                    </option>

                  </select>

                </div>

              </div>

            </div>
          )}


          {/* ABOUT US */}

          {activeTab === "about" && (
            <div>

              <div className="profile-section-heading">

                <h2>About TrustVision</h2>

                <p>
                  Application information, security and legal documents.
                </p>

              </div>


              <div className="about-app-card">

                <div className="about-logo">
                  <ShieldCheck size={32} />
                </div>

                <div>

                  <h3>TrustVision</h3>

                  <p>
                    AI-assisted Identity Verification System
                  </p>

                  <span>
                    Version 1.0.0
                  </span>

                </div>

              </div>


              <div className="about-options">

                <button className="about-option">

                  <div className="about-option-icon">
                    <FileText size={19} />
                  </div>

                  <div>

                    <strong>
                      Application Licence
                    </strong>

                    <span>
                      View application licence
                    </span>

                  </div>

                  <ChevronRight size={18} />

                </button>


                <button className="about-option">

                  <div className="about-option-icon">
                    <ShieldCheck size={19} />
                  </div>

                  <div>

                    <strong>
                      App Security
                    </strong>

                    <span>
                      Security information
                    </span>

                  </div>

                  <ChevronRight size={18} />

                </button>


                <button className="about-option">

                  <div className="about-option-icon">
                    <FileText size={19} />
                  </div>

                  <div>

                    <strong>
                      Application Documents
                    </strong>

                    <span>
                      View supporting documents
                    </span>

                  </div>

                  <ChevronRight size={18} />

                </button>


                <button className="about-option">

                  <div className="about-option-icon">
                    <ScrollText size={19} />
                  </div>

                  <div>

                    <strong>
                      Terms & Conditions
                    </strong>

                    <span>
                      View terms and conditions
                    </span>

                  </div>

                  <ChevronRight size={18} />

                </button>

              </div>

            </div>
          )}

        </section>

      </div>

    </main>
  );
}