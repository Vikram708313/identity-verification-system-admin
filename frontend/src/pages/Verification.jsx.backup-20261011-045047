import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Html5Qrcode } from "html5-qrcode";

import {
  ScanFace,
  FileCheck,
  QrCode,
  CheckCircle2,
  ChevronRight,
  ArrowLeft,
  ShieldCheck,
  Upload,
  RotateCcw,
  Sparkles,
  AlertTriangle,
  CircleAlert,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import api from "../services/api";
import "./Verification.css";

const API_BASE_URL = "http://127.0.0.1:8000";

export default function Verification() {
  const [step, setStep] = useState("face");
  const [faceVerified, setFaceVerified] = useState(false);
  const [method, setMethod] = useState(null);

  const [personId, setPersonId] = useState(null);
  const [selectedPerson, setSelectedPerson] = useState(null);

  const [faceScore, setFaceScore] = useState(null);
  const [documentResult, setDocumentResult] = useState(null);
  const [qrResult, setQrResult] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [decision, setDecision] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [documentFile, setDocumentFile] = useState(null);

  const qrScannerRef = useRef(null);
  const qrScanningRef = useRef(false);
  const qrProcessingRef = useRef(false);

  const faceVideoRef = useRef(null);
  const faceStreamRef = useRef(null);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("access_token");

    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  };

 
  // =====================================================
  // STEP 1 - FACE
  // =====================================================

  const startFaceVerification = async () => {

    setError("");
    setLoading(true);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
        },
        audio: false,
      });

      faceStreamRef.current = stream;

      if (faceVideoRef.current) {
        faceVideoRef.current.srcObject = stream;
        await faceVideoRef.current.play();
      }

      setTimeout(async () => {
        try {
          if (!faceVideoRef.current) {
            throw new Error("Camera is not available.");
          }

          const video = faceVideoRef.current;

          const captureFrame = () =>
            new Promise((resolve) => {
              const canvas = document.createElement("canvas");

              canvas.width = video.videoWidth;
              canvas.height = video.videoHeight;

              const context = canvas.getContext("2d");

              context.drawImage(
                video,
                0,
                0,
                canvas.width,
                canvas.height
              );

              canvas.toBlob(
                resolve,
                "image/jpeg",
                0.9
              );
            });

          const frames = [];

          for (let i = 0; i < 5; i++) {
            const frame = await captureFrame();

            if (frame) {
              frames.push(frame);
            }

            await new Promise((resolve) =>
              setTimeout(resolve, 150)
            );
          }

          if (frames.length < 3) {
            throw new Error(
              "Unable to capture enough camera frames."
            );
          }

          const formData = new FormData();

          formData.append(
            "verification_image",
            frames[frames.length - 1],
            "live-face.jpeg"
          );

          frames.forEach((frame, index) => {
            formData.append(
              "liveness_frames",
              frame,
              `liveness-${index}.jpeg`
            );
          });

          const response = await axios.post(
            `${API_BASE_URL}/face/compare?person_id=${personId}`,
            formData,
            {
              headers: {
                Authorization: `Bearer ${localStorage.getItem(
                  "access_token"
                )}`,
              },
            }
          );

          const score = response.data.match_score;

          setFaceScore(score);
          setFaceVerified(response.data.verified);

          if (!response.data.verified) {
            setError(
              `Face verification failed. Match score: ${score}%`
            );
          }
        } catch (err) {
          handleApiError(err);
        } finally {
          if (faceStreamRef.current) {
            faceStreamRef.current
              .getTracks()
              .forEach((track) => track.stop());

            faceStreamRef.current = null;
          }

          setLoading(false);
        }
      }, 500);
    } catch (err) {
      console.error(err);

      setLoading(false);

      setError(
        "Unable to access the camera. Please allow camera permission and try again."
      );
    }
  };

  // =====================================================
  // METHOD
  // =====================================================

  const selectMethod = (selectedMethod) => {

    setMethod(selectedMethod);
    setError("");
    setDocumentResult(null);
    setQrResult(null);
    setStep(selectedMethod);
  };

  // =====================================================
  // DOCUMENT VERIFICATION
  // =====================================================

  const analyzeDocument = async () => {
    if (!personId) {
      setError("Please select a registered person first.");
      return;
    }

    if (!documentFile) {
      setError("Please select an identity document first.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const formData = new FormData();

      formData.append("person_id", String(personId));
      formData.append("document_type", "AADHAAR");
      formData.append(
        "document_number",
        "DEMO-AADHAAR-001"
      );
      formData.append("file", documentFile);

      const token = localStorage.getItem("access_token");

      const response = await axios.post(
  `${API_BASE_URL}/face/compare`,
  formData,
  {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token")}`,
    },
  }
);

const score = response.data.match_score;

setFaceScore(score);
setFaceVerified(response.data.verified);

if (response.data.verified && response.data.person) {
  setPersonId(response.data.person.id);
  setSelectedPerson(response.data.person);
} else {
  setPersonId(null);
  setSelectedPerson(null);
  setError(
    response.data.message ||
      `No confident face match found. Score: ${score}%`
  );
}

      setDocumentResult(response.data);

      if (!response.data.verified) {
        setError(
          response.data.reason ||
            "Document verification requires review."
        );

        if (response.data.status === "FAIL") {
          setLoading(false);
          return;
        }
      }

      await runAIAnalysis(
        "document",
        response.data
      );
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // QR VERIFICATION
  // =====================================================

  const analyzeQR = async (scannedToken) => {
    if (!scannedToken || qrProcessingRef.current) {
      return;
    }

    qrProcessingRef.current = true;

    setError("");
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/qr/verify`,
        {
          token: scannedToken.trim(),
        },
        {
          headers: getAuthHeaders(),
        }
      );

      setQrResult(response.data);

      if (!response.data.verified) {
        setError(
          response.data.reason ||
            "QR verification failed."
        );

        return;
      }

      await runAIAnalysis("qr", response.data);
    } catch (err) {
      handleApiError(err);
    } finally {
      qrProcessingRef.current = false;
      setLoading(false);
    }
  };

  // =====================================================
  // QR CAMERA SCANNER
  // =====================================================

  const stopQRScanner = async () => {
    qrScanningRef.current = false;

    if (!qrScannerRef.current) {
      return;
    }

    try {
      if (qrScannerRef.current.isScanning) {
        await qrScannerRef.current.stop();
      }
    } catch (err) {
      console.warn(
        "QR scanner stop warning:",
        err
      );
    }

    try {
      await qrScannerRef.current.clear();
    } catch (err) {
      console.warn(
        "QR scanner clear warning:",
        err
      );
    }

    qrScannerRef.current = null;
  };

  const startQRScanner = async () => {
    if (
      qrScannerRef.current ||
      qrScanningRef.current
    ) {
      return;
    }

    setError("");

    try {
      const scanner = new Html5Qrcode("qr-reader");

      qrScannerRef.current = scanner;
      qrScanningRef.current = true;

      await scanner.start(
        {
          facingMode: "environment",
        },
        {
          fps: 10,
          qrbox: {
            width: 250,
            height: 250,
          },
        },
        async (decodedText) => {
          if (qrProcessingRef.current) {
            return;
          }

          await stopQRScanner();

          await analyzeQR(decodedText);
        },
        () => {
          // Normal scanning frame failure.
        }
      );
    } catch (err) {
      console.error(
        "QR scanner error:",
        err
      );

      qrScanningRef.current = false;
      qrScannerRef.current = null;

      setError(
        "Unable to access the camera. Please allow camera permission and try again."
      );
    }
  };

  useEffect(() => {
    if (step === "qr") {
      const timer = setTimeout(() => {
        startQRScanner();
      }, 300);

      return () => {
        clearTimeout(timer);
        stopQRScanner();
      };
    }

    stopQRScanner();

    return undefined;
  }, [step]);

  // =====================================================
  // AI ANALYSIS
  // =====================================================

  const runAIAnalysis = async (
    verificationMethod,
    secondaryResult
  ) => {
    const documentScore =
      verificationMethod === "document"
        ? secondaryResult?.document_match_score ??
          null
        : null;

    const qrScore =
      verificationMethod === "qr"
        ? secondaryResult?.verification?.qr_valid
          ? 100
          : 0
        : null;

    const response = await axios.post(
      `${API_BASE_URL}/verification/analyze`,
      {
        person_id: personId,
        verification_method:
          verificationMethod,
        face_match_score:
          faceScore ?? 97,
        document_match_score:
          documentScore,
        qr_match_score: qrScore,
        completeness_score: 100,
        consistency_score:
          verificationMethod === "document"
            ? documentScore ?? 100
            : qrScore ?? 100,
      },
      {
        headers: getAuthHeaders(),
      }
    );

    setAnalysisResult(response.data);
    setDecision(null);
    setStep("result");
  };

  // =====================================================
  // FINAL ADMIN DECISION
  // =====================================================

  const submitDecision = async (
    selectedDecision
  ) => {
    if (!analysisResult?.verification_id) {
      setError(
        "Verification record is missing. Please run the analysis again."
      );
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await axios.post(
        `${API_BASE_URL}/verification/${analysisResult.verification_id}/decision`,
        {
          decision: selectedDecision,
        },
        {
          headers: getAuthHeaders(),
        }
      );

      setDecision(response.data.decision);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // API ERROR HANDLING
  // =====================================================

  const handleApiError = (err) => {
    console.error(err);

    if (err.response?.status === 401) {
      setError(
        "Your session has expired. Please log in again."
      );
      return;
    }

    if (err.response?.data?.detail) {
      setError(err.response.data.detail);
      return;
    }

    if (err.message) {
      setError(err.message);
      return;
    }

    setError(
      "Something went wrong during verification."
    );
  };

  // =====================================================
  // RESET
  // =====================================================

  const startNewVerification = async () => {
    await stopQRScanner();

    if (faceStreamRef.current) {
      faceStreamRef.current
        .getTracks()
        .forEach((track) => track.stop());

      faceStreamRef.current = null;
    }

    setStep("face");
    setFaceVerified(false);
    setMethod(null);

    setPersonId(null);
    setSelectedPerson(null);

    setFaceScore(null);
    setDocumentResult(null);
    setDocumentFile(null);
    setQrResult(null);
    setAnalysisResult(null);
    setDecision(null);

    setError("");
    setLoading(false);

    qrProcessingRef.current = false;
  };

  // =====================================================
  // BACK
  // =====================================================

  const goBack = async () => {
    setError("");

    if (
      step === "document" ||
      step === "qr"
    ) {
      await stopQRScanner();
      setStep("method");
      return;
    }

    if (step === "method") {
      setStep("face");
    }
  };

  const continueAfterFace = () => {
    if (!personId) {
      setError(
        "Please select a registered person first."
      );
      return;
    }

    setError("");
    setStep("method");
  };

  return (
    <div className="verification-app">
      <Sidebar />

      <main className="verification-main">

        {/* HEADER */}

        <header className="verification-header">
          <div>
            <div className="ai-page-title">
              <Sparkles size={20} />
              <span>
                AI-POWERED VERIFICATION
              </span>
            </div>

            <h1>Verify with AI</h1>

            <p>
              Verify an identity and receive an
              AI-assisted risk assessment with the
              reasons behind the result.
            </p>
          </div>

          <div className="verification-security">
            <ShieldCheck size={18} />
            <span>
              Secure Verification
            </span>
          </div>
        </header>

        {/* ERROR */}

        {error && (
          <div
            style={{
              marginBottom: "18px",
              padding: "14px 16px",
              borderRadius: "12px",
              border: "1px solid #fca5a5",
              background: "#fef2f2",
              color: "#991b1b",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <CircleAlert size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* STEPS */}

        <div className="verification-steps">

          <StepIndicator
            number="1"
            title="Face"
            active={step === "face"}
            completed={faceVerified}
          />

          <div className="step-line" />

          <StepIndicator
            number="2"
            title="Document / QR"
            active={
              step === "method" ||
              step === "document" ||
              step === "qr"
            }
          />

          <div className="step-line" />

          <StepIndicator
            number="3"
            title="AI Analysis"
            active={step === "result"}
          />

        </div>

        {/* ================================================= */}
        {/* FACE */}
        {/* ================================================= */}

        {step === "face" && (
          <section className="verification-card">

            <div
              style={{
                marginBottom: "24px",
              }}
            >
              
              
            </div>

            <div className="verification-card-header">
              <div>
                <p className="card-eyebrow">
                  STEP 1
                </p>

                <h2>
                  Face Verification
                </h2>

                <p>
                  Verify the person's face before
                  continuing with document or QR
                  verification.
                </p>
              </div>

              <div className="verification-card-icon">
                <ScanFace size={26} />
              </div>
            </div>

            {!faceVerified && (
              <div className="camera-area">

                <div className="face-camera-frame">
                  <video
                    ref={faceVideoRef}
                    className="face-camera-video"
                    autoPlay
                    muted
                    playsInline
                    width="640"
                    height="480"
                  />

                  <div className="face-corner top-left" />
                  <div className="face-corner top-right" />
                  <div className="face-corner bottom-left" />
                  <div className="face-corner bottom-right" />

                  {!faceVideoRef.current?.srcObject && (
                    <ScanFace size={58} />
                  )}
                </div>

                <strong>
                  Position the face inside the frame
                </strong>

                <span>
                  Make sure the person's face is clearly
                  visible.
                </span>

                <button
                  className="primary-verification-button"
                  onClick={
                    startFaceVerification
                  }
                  disabled={loading}
                  
                >
                  <ScanFace size={18} />

                  {loading
                    ? "Verifying..."
                    : "Start Face Verification"}
                </button>

              </div>
            )}

            {faceVerified && (
              <div className="face-success-area">

                <div className="success-circle">
                  <CheckCircle2 size={38} />
                </div>

                <h3>
                  Face Verification Successful
                </h3>

                <p>
                  The person's face has been successfully
                  matched.
                </p>

                <div className="face-person-card">

                  <div className="face-person-avatar">
                    {getPersonInitial(
                      selectedPerson
                    )}
                  </div>

                  <div>
                    <strong>
                      {selectedPerson?.full_name ||
                        "Unknown Person"}
                    </strong>

                    <span>
                      User ID #
                      {selectedPerson?.id ||
                        "-"}{" "}
                      · Face match{" "}
                      {faceScore}%
                    </span>
                  </div>

                  <div className="face-match-score">
                    <strong>
                      {faceScore}%
                    </strong>

                    <span>
                      Face Match
                    </span>
                  </div>

                </div>

                <button
                  className="primary-verification-button"
                  onClick={
                    continueAfterFace
                  }
                >
                  Continue
                  <ChevronRight size={18} />
                </button>

              </div>
            )}

          </section>
        )}

        {/* ================================================= */}
        {/* METHOD */}
        {/* ================================================= */}

        {step === "method" && (
          <section className="verification-card">

            <BackButton
              onClick={goBack}
            />

            <div className="verification-success-strip">
              <CheckCircle2 size={19} />

              <div>
                <strong>
                  Face verification completed
                </strong>

                <span>
                  User ID #
                  {selectedPerson?.id ||
                    "-"}{" "}
                  · Face match{" "}
                  {faceScore}%
                </span>
              </div>
            </div>

            <div className="method-heading">

              <p className="card-eyebrow">
                STEP 2
              </p>

              <h2>
                Choose Verification Method
              </h2>

              <p>
                Select one additional method to verify
                the identity.
              </p>

            </div>

            <div className="verification-method-grid">

              <button
                className="verification-method-card"
                onClick={() =>
                  selectMethod(
                    "document"
                  )
                }
              >
                <div className="method-icon">
                  <FileCheck size={28} />
                </div>

                <div>
                  <strong>
                    Document Verification
                  </strong>

                  <span>
                    Upload or scan an identity
                    document.
                  </span>
                </div>

                <ChevronRight size={20} />
              </button>

              <button
                className="verification-method-card"
                onClick={() =>
                  selectMethod("qr")
                }
              >
                <div className="method-icon">
                  <QrCode size={28} />
                </div>

                <div>
                  <strong>
                    QR Verification
                  </strong>

                  <span>
                    Scan the identity QR code.
                  </span>
                </div>

                <ChevronRight size={20} />
              </button>

            </div>

          </section>
        )}

        {/* ================================================= */}
        {/* DOCUMENT */}
        {/* ================================================= */}

        {step === "document" && (
          <section className="verification-card">

            <BackButton
              onClick={goBack}
            />

            <div className="verification-card-header">

              <div>
                <p className="card-eyebrow">
                  STEP 2 · DOCUMENT
                </p>

                <h2>
                  Document Verification
                </h2>

                <p>
                  Upload the identity document to verify it
                  against the registered identity.
                </p>
              </div>

              <div className="verification-card-icon">
                <FileCheck size={26} />
              </div>

            </div>

            <VerifiedPerson
              faceScore={faceScore}
              selectedPerson={selectedPerson}
            />

            <div className="document-upload-area">

              <div className="upload-icon">
                <Upload size={30} />
              </div>

              <strong>
                Select Identity Document
              </strong>

              <span>
                Upload the registered Aadhaar document
                as PDF, JPG, JPEG, or PNG.
              </span>

              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(event) => {
                  const file =
                    event.target.files?.[0] ||
                    null;

                  setDocumentFile(file);
                  setError("");
                }}
              />

              {documentFile && (
                <span>
                  Selected:{" "}
                  {documentFile.name}
                </span>
              )}

              <button
                className="secondary-verification-button"
                onClick={
                  analyzeDocument
                }
                disabled={
                  loading ||
                  !documentFile ||
                  !personId
                }
              >
                <FileCheck size={17} />

                {loading
                  ? "Verifying..."
                  : "Verify Document"}
              </button>

            </div>

            <div className="ai-info-box">

              <Sparkles size={17} />

              <span>
                The uploaded document is hashed and
                compared with the registered document
                before risk analysis.
              </span>

            </div>

          </section>
        )}

        {/* ================================================= */}
        {/* QR */}
        {/* ================================================= */}

        {step === "qr" && (
          <section className="verification-card">

            <BackButton
              onClick={goBack}
            />

            <div className="verification-card-header">

              <div>
                <p className="card-eyebrow">
                  STEP 2 · QR
                </p>

                <h2>
                  QR Verification
                </h2>

                <p>
                  Scan the QR code belonging to the
                  face-verified person.
                </p>
              </div>

              <div className="verification-card-icon">
                <QrCode size={26} />
              </div>

            </div>

            <VerifiedPerson
              faceScore={faceScore}
              selectedPerson={selectedPerson}
            />

            <div className="qr-scanner-area">

              <div
                id="qr-reader"
                style={{
                  width: "100%",
                  maxWidth: "500px",
                  margin: "0 auto",
                }}
              />

              <strong>
                Position QR code inside the frame
              </strong>

              <span>
                Make sure the QR code is clearly visible.
              </span>

              {loading && (
                <div
                  style={{
                    marginTop: "12px",
                  }}
                >
                  Verifying QR code...
                </div>
              )}

            </div>

            <div className="ai-info-box">

              <Sparkles size={17} />

              <span>
                The QR token will be checked against the
                registered identity and then passed to the
                risk analysis engine.
              </span>

            </div>

          </section>
        )}

        {/* ================================================= */}
        {/* RESULT */}
        {/* ================================================= */}

        {step === "result" && (
          <AIResult
            method={method}
            result={analysisResult}
            documentResult={documentResult}
            qrResult={qrResult}
            decision={decision}
            loading={loading}
            onDecision={submitDecision}
            onNewVerification={
              startNewVerification
            }
          />
        )}

      </main>
    </div>
  );
}


/* ===================================================== */
/* STEP INDICATOR */
/* ===================================================== */

function StepIndicator({
  number,
  title,
  active,
  completed,
}) {
  return (
    <div
      className={`verification-step ${
        active ? "active" : ""
      } ${
        completed ? "completed" : ""
      }`}
    >
      <div className="step-number">
        {completed ? (
          <CheckCircle2 size={16} />
        ) : (
          number
        )}
      </div>

      <span>{title}</span>
    </div>
  );
}


/* ===================================================== */
/* BACK BUTTON */
/* ===================================================== */

function BackButton({ onClick }) {
  return (
    <button
      className="verification-back"
      onClick={onClick}
    >
      <ArrowLeft size={16} />
      Back
    </button>
  );
}


/* ===================================================== */
/* PERSON INITIAL */
/* ===================================================== */

function getPersonInitial(person) {
  if (!person?.full_name) {
    return "?";
  }

  return person.full_name
    .trim()
    .charAt(0)
    .toUpperCase();
}


/* ===================================================== */
/* VERIFIED PERSON */
/* ===================================================== */

function VerifiedPerson({
  faceScore,
  selectedPerson,
}) {
  return (
    <div className="verified-person">

      <div className="verified-person-avatar">
        {getPersonInitial(
          selectedPerson
        )}
      </div>

      <div>
        <span>
          Face verified person
        </span>

        <strong>
          {selectedPerson?.full_name ||
            "Unknown Person"}
        </strong>

        <small>
          User ID #
          {selectedPerson?.id ||
            "-"}{" "}
          · Face match{" "}
          {faceScore}%
        </small>
      </div>

      <CheckCircle2 size={20} />

    </div>
  );
}


/* ===================================================== */
/* AI RESULT */
/* ===================================================== */

function AIResult({
  method,
  result,
  documentResult,
  qrResult,
  decision,
  loading,
  onDecision,
  onNewVerification,
}) {
  const riskScore =
    result?.risk?.score ?? 0;

  const riskLevel =
    result?.risk?.level ?? "UNKNOWN";

  const riskLabel =
    riskLevel === "LOW"
      ? "Low Risk"
      : riskLevel === "MEDIUM"
      ? "Medium Risk"
      : riskLevel === "HIGH"
      ? "High Risk"
      : "Unknown";

  const signals =
    result?.signals ?? {};

  const reasons =
    result?.reasons ?? [];

  const documentScore =
    signals.document_match_score;

  const qrScore =
    signals.qr_match_score;

  return (
    <section className="ai-result-page">

      {/* RESULT HEADER */}

      <div className="ai-result-header">

        <div className="ai-result-title">

          <div className="ai-sparkle-icon">
            <Sparkles size={24} />
          </div>

          <div>
            <p className="card-eyebrow">
              AI ANALYSIS COMPLETE
            </p>

            <h2>
              Identity Risk Assessment
            </h2>

            <p>
              The backend analyzed the available
              verification signals.
            </p>
          </div>

        </div>

        <div className="ai-analysis-badge">
          <Sparkles size={15} />
          AI Assisted
        </div>

      </div>


      {/* RISK SUMMARY */}

      <div className="risk-summary-grid">

        <div className="risk-score-card">

          <div className="risk-score-top">

            <div>
              <span>
                Overall Risk
              </span>

              <strong>
                {riskScore}%
              </strong>
            </div>

            <div className="risk-circle">
              <ShieldCheck size={27} />
            </div>

          </div>

          <div className="risk-bar">

            <div
              className="risk-bar-fill"
              style={{
                width: `${riskScore}%`,
              }}
            />

          </div>

          <div className="risk-score-bottom">

            <span>
              0% · Lower Risk
            </span>

            <strong>
              {riskLabel}
            </strong>

            <span>
              100% · Higher Risk
            </span>

          </div>

        </div>


        {/* IDENTITY */}

        <div className="ai-identity-card">

          <div className="result-avatar">
            {getPersonInitial(
              result?.person
            )}
          </div>

          <div>

            <span>
              Verified Identity
            </span>

            <strong>
              {result?.person?.full_name ||
                "Unknown"}
            </strong>

            <small>
              User ID #
              {result?.person?.id ??
                "-"}
            </small>

          </div>

          <div className="approved-badge">
            <CheckCircle2 size={14} />
            Matched
          </div>

        </div>

      </div>


      {/* AI EXPLANATION */}

      <div className="ai-explanation-card">

        <div className="ai-section-heading">

          <div className="ai-heading-icon">
            <Sparkles size={19} />
          </div>

          <div>
            <p>
              AI ASSISTANT
            </p>

            <h3>
              Why is the risk{" "}
              {riskScore}%?
            </h3>
          </div>

        </div>

        <div className="ai-explanation-text">

          {reasons.length > 0 ? (
            reasons.map(
              (reason, index) => (
                <p key={index}>
                  {reason}
                </p>
              )
            )
          ) : (
            <p>
              No additional risk factors were returned
              by the verification engine.
            </p>
          )}

        </div>

      </div>


      {/* VERIFICATION SIGNALS */}

      <div className="ai-section">

        <div className="ai-section-title">

          <div>
            <p>
              VERIFICATION SIGNALS
            </p>

            <h3>
              Factors considered by AI
            </h3>
          </div>

          <span>
            {method === "qr"
              ? "QR verification"
              : "Document verification"}
          </span>

        </div>


        <div className="ai-signal-list">

          <AISignal
            icon={
              <ScanFace size={19} />
            }
            name="Face Match"
            value={
              signals.face_match_score != null
                ? `${signals.face_match_score}%`
                : "N/A"
            }
            status={
              signals.face_match_score >= 85
                ? "Strong match"
                : "Review required"
            }
            type={
              signals.face_match_score >= 85
                ? "positive"
                : "warning"
            }
          />


          {method === "document" && (
            <AISignal
              icon={
                <FileCheck size={19} />
              }
              name="Document Match"
              value={
                documentScore != null
                  ? `${documentScore}%`
                  : "N/A"
              }
              status={
                documentScore >= 85
                  ? "Strong match"
                  : documentScore >= 60
                  ? "Review required"
                  : "Mismatch"
              }
              type={
                documentScore >= 85
                  ? "positive"
                  : "warning"
              }
            />
          )}


          {method === "qr" && (
            <AISignal
              icon={
                <QrCode size={19} />
              }
              name="QR Match"
              value={
                qrScore != null
                  ? `${qrScore}%`
                  : "N/A"
              }
              status={
                qrResult?.verified
                  ? "Valid QR"
                  : "Invalid QR"
              }
              type={
                qrResult?.verified
                  ? "positive"
                  : "warning"
              }
            />
          )}


          <AISignal
            icon={
              <ShieldCheck size={19} />
            }
            name="Identity Database"
            value={
              signals.registered_document_count >
              0
                ? "Matched"
                : "Found"
            }
            status={
              signals.registered_document_count >
              0
                ? "Registered evidence found"
                : "Person found in database"
            }
            type="positive"
          />


          <AISignal
            icon={
              <ShieldCheck size={19} />
            }
            name="Completeness"
            value={
              signals.completeness_score != null
                ? `${signals.completeness_score}%`
                : "N/A"
            }
            status={
              signals.completeness_score >= 90
                ? "Complete identity"
                : "Incomplete record"
            }
            type={
              signals.completeness_score >= 90
                ? "positive"
                : "warning"
            }
          />


          <AISignal
            icon={
              <ShieldCheck size={19} />
            }
            name="Consistency"
            value={
              signals.consistency_score != null
                ? `${signals.consistency_score}%`
                : "N/A"
            }
            status={
              signals.consistency_score >= 90
                ? "Consistent"
                : "Review required"
            }
            type={
              signals.consistency_score >= 90
                ? "positive"
                : "warning"
            }
          />

        </div>

      </div>


      {/* RISK CAUSES */}

      <div className="ai-causes-card">

        <div className="ai-section-heading">

          <div className="ai-heading-icon warning">
            <AlertTriangle size={19} />
          </div>

          <div>
            <p>
              RISK FACTORS
            </p>

            <h3>
              Causes contributing to the risk
            </h3>
          </div>

        </div>


        <div className="risk-cause-list">

          {reasons.length > 0 ? (
            reasons.map(
              (reason, index) => (
                <RiskCause
                  key={index}
                  number={String(
                    index + 1
                  ).padStart(2, "0")}
                  title="Verification signal"
                  description={reason}
                />
              )
            )
          ) : (
            <RiskCause
              number="01"
              title="No significant risk factor"
              description="The configured prototype thresholds did not identify an additional risk factor."
            />
          )}

        </div>

      </div>


      {/* ADMIN DECISION */}

      <div className="ai-review-card">

        <div className="ai-review-icon">
          <CircleAlert size={21} />
        </div>

        <div>

          <p>
            ADMIN DECISION
          </p>

          <strong>
            Human review is required for the final decision
          </strong>

          <span>
            The risk engine provides an assessment only.
            The administrator makes the final verification
            decision.
          </span>

          {decision && (
            <strong
              style={{
                marginTop: "10px",
                display: "block",
              }}
            >
              Decision recorded:{" "}
              {decision}
            </strong>
          )}

        </div>

      </div>


      {/* DECISION BUTTONS */}

      {!decision && (
        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginTop: "20px",
          }}
        >

          <button
            className="primary-verification-button"
            onClick={() =>
              onDecision("APPROVE")
            }
            disabled={loading}
          >
            <CheckCircle2 size={17} />

            {loading
              ? "Saving..."
              : "Approve"}
          </button>

          <button
            className="secondary-verification-button"
            onClick={() =>
              onDecision("REVIEW")
            }
            disabled={loading}
          >
            <CircleAlert size={17} />
            Send to Review
          </button>

          <button
            className="secondary-verification-button"
            onClick={() =>
              onDecision("REJECT")
            }
            disabled={loading}
          >
            <AlertTriangle size={17} />
            Reject
          </button>

        </div>
      )}


      {/* NEW VERIFICATION */}

      <button
        className="new-verification-button"
        onClick={
          onNewVerification
        }
      >
        <RotateCcw size={17} />
        Start New AI Verification
      </button>

    </section>
  );
}


/* ===================================================== */
/* AI SIGNAL */
/* ===================================================== */

function AISignal({
  icon,
  name,
  value,
  status,
  type,
}) {
  return (
    <div className="ai-signal">

      <div className="ai-signal-icon">
        {icon}
      </div>

      <div className="ai-signal-name">

        <strong>
          {name}
        </strong>

        <span>
          {status}
        </span>

      </div>

      <div
        className={`ai-signal-value ${type}`}
      >
        {value}
      </div>

    </div>
  );
}


/* ===================================================== */
/* RISK CAUSE */
/* ===================================================== */

function RiskCause({
  number,
  title,
  description,
}) {
  return (
    <div className="risk-cause">

      <div className="risk-cause-number">
        {number}
      </div>

      <div>

        <strong>
          {title}
        </strong>

        <span>
          {description}
        </span>

      </div>

    </div>
  );
}