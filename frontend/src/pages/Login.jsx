import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Lock,
  User,
  Eye,
  EyeOff,
  ShieldCheck,
  FileCheck,
  ScanFace,
  ArrowRight,
} from "lucide-react";

import api from "../services/api";
import "./Login.css";

export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (event) => {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const formData = new URLSearchParams();

      formData.append("username", username);
      formData.append("password", password);

      const response = await api.post("/auth/login", formData, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });

      localStorage.setItem(
        "access_token",
        response.data.access_token
      );

      localStorage.setItem(
        "role",
        response.data.role
      );

      navigate("/dashboard");
    } catch (err) {
      console.error("Login failed:", err);

      setError(
        err.response?.data?.detail ||
          "Invalid username or password."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="trust-login">

      {/* Subtle logo watermark */}
      <img
        className="trust-watermark"
        src="/trustvision-logo.png"
        alt=""
        aria-hidden="true"
      />

      {/* =====================================================
          LEFT SIDE
          ===================================================== */}

      <section className="trust-left">

        <div className="trust-left-content">

          {/* ACTUAL LOGO FROM PUBLIC FOLDER */}
          <img
            className="trust-main-logo"
            src="/trustvision-logo.png"
            alt="TrustVision"
          />

          <p className="trust-subtitle">
            AI-Powered Fake Identity &amp;
            <br />
            Document Screening System
          </p>

          <div className="trust-line" />

          <p className="trust-kicker">
            IDENTITY SCREENING
          </p>

          <h1 className="trust-heading">
            Verify identities.
            <br />
            <span>Build trust.</span>
          </h1>

          <p className="trust-description">
            Advanced identity and document screening
            tools designed to detect suspicious
            identities and fraudulent documents.
          </p>

          {/* Feature list */}

          <div className="trust-features">

            <div className="trust-feature">
              <div className="trust-feature-icon">
                <ShieldCheck size={22} />
              </div>

              <div>
                <strong>Secure Authentication</strong>
                <span>JWT protected access</span>
              </div>
            </div>

            <div className="trust-feature">
              <div className="trust-feature-icon">
                <FileCheck size={22} />
              </div>

              <div>
                <strong>Document Verification</strong>
                <span>Validate identity documents</span>
              </div>
            </div>

            <div className="trust-feature">
              <div className="trust-feature-icon">
                <ScanFace size={22} />
              </div>

              <div>
                <strong>Face Verification</strong>
                <span>Secure biometric matching</span>
              </div>
            </div>

          </div>

          <div className="trust-environment">
            <ShieldCheck size={18} />
            <span>Local demonstration environment</span>
          </div>

        </div>

        {/* Decorative blue area */}

        <div className="trust-blue-shape">
          <div className="trust-glow-circle" />
          <div className="trust-glow-circle second" />
        </div>

      </section>


      {/* =====================================================
          RIGHT SIDE
          ===================================================== */}

      <section className="trust-right">

        <div className="trust-card">

          {/* Logo inside login card */}

          <img
            className="trust-card-logo"
            src="/trustvision-logo.png"
            alt="TrustVision"
          />

          <div className="trust-card-heading">
            <h2>Welcome back</h2>

            <p>
              Sign in to your administrator account
            </p>
          </div>


          {/* LOGIN FORM */}

          <form
            className="trust-form"
            onSubmit={handleLogin}
          >

            {/* USERNAME */}

            <div className="trust-form-group">

              <label htmlFor="username">
                Username
              </label>

              <div className="trust-input">

                <div className="trust-input-icon">
                  <User size={20} />
                </div>

                <input
                  id="username"
                  type="text"
                  value={username}
                  onChange={(event) =>
                    setUsername(event.target.value)
                  }
                  placeholder="Enter username"
                  autoComplete="off"
                  required
                />

              </div>

            </div>


            {/* PASSWORD */}

            <div className="trust-form-group">

              <label htmlFor="password">
                Password
              </label>

              <div className="trust-input">

                <div className="trust-input-icon">
                  <Lock size={20} />
                </div>

                <input
                  id="password"
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter password"
                  autoComplete="new-password"
                  required
                />

                <button
                  type="button"
                  className="trust-password-toggle"
                  onClick={() =>
                    setShowPassword(!showPassword)
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? (
                    <EyeOff size={20} />
                  ) : (
                    <Eye size={20} />
                  )}
                </button>

              </div>

            </div>


            {/* ERROR */}

            {error && (
              <div className="trust-error">
                {error}
              </div>
            )}


            {/* SIGN IN */}

            <button
              type="submit"
              className="trust-signin"
              disabled={loading}
            >

              {loading ? (
                <span>Signing in...</span>
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight size={21} />
                </>
              )}

            </button>

          </form>


          {/* SECURITY */}

          <div className="trust-security">
            <ShieldCheck size={19} />
            <span>
              Protected administrator access
            </span>
          </div>


          {/* FOOTER */}

          <div className="trust-footer">
            TrustVision Identity Screening
          </div>

        </div>

      </section>

    </main>
  );
}