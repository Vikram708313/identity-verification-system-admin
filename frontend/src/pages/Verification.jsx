import { useState } from "react";
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
import "./Verification.css";

export default function Verification() {
  const [step, setStep] = useState("face");
  const [faceVerified, setFaceVerified] = useState(false);
  const [method, setMethod] = useState(null);

  const startFaceVerification = () => {
    // Temporary simulation.
    setFaceVerified(true);
  };

  const continueAfterFace = () => {
    setStep("method");
  };

  const selectMethod = (selectedMethod) => {
    setMethod(selectedMethod);
    setStep(selectedMethod);
  };

  const completeVerification = () => {
    setStep("result");
  };

  const startNewVerification = () => {
    setStep("face");
    setFaceVerified(false);
    setMethod(null);
  };

  const goBack = () => {
    if (step === "document" || step === "qr") {
      setStep("method");
      return;
    }

    if (step === "method") {
      setStep("face");
    }
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
              <span>AI-POWERED VERIFICATION</span>
            </div>

            <h1>Verify with AI</h1>

            <p>
              Verify an identity and receive an AI-assisted
              risk assessment with the reasons behind the result.
            </p>
          </div>

          <div className="verification-security">
            <ShieldCheck size={18} />
            <span>Secure Verification</span>
          </div>
        </header>

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

        {/* FACE VERIFICATION */}
        {step === "face" && (
          <section className="verification-card">

            <div className="verification-card-header">
              <div>
                <p className="card-eyebrow">STEP 1</p>

                <h2>Face Verification</h2>

                <p>
                  Verify the person's face before continuing
                  with document or QR verification.
                </p>
              </div>

              <div className="verification-card-icon">
                <ScanFace size={26} />
              </div>
            </div>

            {!faceVerified && (
              <div className="camera-area">

                <div className="face-camera-frame">

                  <div className="face-corner top-left" />
                  <div className="face-corner top-right" />
                  <div className="face-corner bottom-left" />
                  <div className="face-corner bottom-right" />

                  <ScanFace size={58} />

                </div>

                <strong>
                  Position the face inside the frame
                </strong>

                <span>
                  Make sure the person's face is clearly visible.
                </span>

                <button
                  className="primary-verification-button"
                  onClick={startFaceVerification}
                >
                  <ScanFace size={18} />
                  Start Face Verification
                </button>

              </div>
            )}

            {faceVerified && (
              <div className="face-success-area">

                <div className="success-circle">
                  <CheckCircle2 size={38} />
                </div>

                <h3>Face Verification Successful</h3>

                <p>
                  The person's face has been successfully matched.
                </p>

                <div className="face-person-card">

                  <div className="face-person-avatar">
                    A
                  </div>

                  <div>
                    <strong>Sample Identity</strong>
                    <span>User ID #001</span>
                  </div>

                  <div className="face-match-score">
                    <strong>97%</strong>
                    <span>Face Match</span>
                  </div>

                </div>

                <button
                  className="primary-verification-button"
                  onClick={continueAfterFace}
                >
                  Continue
                  <ChevronRight size={18} />
                </button>

              </div>
            )}

          </section>
        )}

        {/* METHOD */}
        {step === "method" && (
          <section className="verification-card">

            <BackButton onClick={goBack} />

            <div className="verification-success-strip">
              <CheckCircle2 size={19} />

              <div>
                <strong>Face verification completed</strong>
                <span>
                  User ID #001 · Face match 97%
                </span>
              </div>
            </div>

            <div className="method-heading">

              <p className="card-eyebrow">STEP 2</p>

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
                onClick={() => selectMethod("document")}
              >
                <div className="method-icon">
                  <FileCheck size={28} />
                </div>

                <div>
                  <strong>
                    Document Verification
                  </strong>

                  <span>
                    Upload or scan an identity document.
                  </span>
                </div>

                <ChevronRight size={20} />
              </button>

              <button
                className="verification-method-card"
                onClick={() => selectMethod("qr")}
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

        {/* DOCUMENT */}
        {step === "document" && (
          <section className="verification-card">

            <BackButton onClick={goBack} />

            <div className="verification-card-header">

              <div>
                <p className="card-eyebrow">
                  STEP 2 · DOCUMENT
                </p>

                <h2>Document Verification</h2>

                <p>
                  Upload the identity document belonging
                  to the face-verified person.
                </p>
              </div>

              <div className="verification-card-icon">
                <FileCheck size={26} />
              </div>

            </div>

            <VerifiedPerson />

            <div className="document-upload-area">

              <div className="upload-icon">
                <Upload size={30} />
              </div>

              <strong>
                Upload Identity Document
              </strong>

              <span>
                Select an Aadhaar, PAN, Passport or
                Driving Licence document.
              </span>

              <button
                className="secondary-verification-button"
                onClick={completeVerification}
              >
                <Upload size={17} />
                Analyze Document
              </button>

            </div>

            <div className="ai-info-box">

              <Sparkles size={17} />

              <span>
                After document verification, AI will analyze
                the available verification signals and explain
                the factors contributing to the risk assessment.
              </span>

            </div>

          </section>
        )}

        {/* QR */}
        {step === "qr" && (
          <section className="verification-card">

            <BackButton onClick={goBack} />

            <div className="verification-card-header">

              <div>
                <p className="card-eyebrow">
                  STEP 2 · QR
                </p>

                <h2>QR Verification</h2>

                <p>
                  Scan the QR code belonging to the
                  face-verified person.
                </p>
              </div>

              <div className="verification-card-icon">
                <QrCode size={26} />
              </div>

            </div>

            <VerifiedPerson />

            <div className="qr-scanner-area">

              <div className="qr-frame">

                <div className="qr-corner qr-top-left" />
                <div className="qr-corner qr-top-right" />
                <div className="qr-corner qr-bottom-left" />
                <div className="qr-corner qr-bottom-right" />

                <QrCode size={70} />

              </div>

              <strong>
                Position QR code inside the frame
              </strong>

              <span>
                Make sure the QR code is clearly visible.
              </span>

              <button
                className="primary-verification-button"
                onClick={completeVerification}
              >
                <QrCode size={18} />
                Analyze QR Code
              </button>

            </div>

            <div className="ai-info-box">

              <Sparkles size={17} />

              <span>
                AI will evaluate the verification signals
                after the QR code is analyzed.
              </span>

            </div>

          </section>
        )}

        {/* AI RESULT */}
        {step === "result" && (
          <AIResult
            method={method}
            onNewVerification={startNewVerification}
          />
        )}

      </main>
    </div>
  );
}


/* -------------------------------- */
/* STEP INDICATOR */
/* -------------------------------- */

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
      } ${completed ? "completed" : ""}`}
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


/* -------------------------------- */
/* BACK BUTTON */
/* -------------------------------- */

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


/* -------------------------------- */
/* VERIFIED PERSON */
/* -------------------------------- */

function VerifiedPerson() {
  return (
    <div className="verified-person">

      <div className="verified-person-avatar">
        A
      </div>

      <div>
        <span>Face verified person</span>

        <strong>
          Sample Identity
        </strong>

        <small>
          User ID #001 · Face match 97%
        </small>
      </div>

      <CheckCircle2 size={20} />

    </div>
  );
}


/* -------------------------------- */
/* AI RESULT */
/* -------------------------------- */

function AIResult({
  method,
  onNewVerification,
}) {

  /*
   * Temporary demonstration values.
   * Later these will come from the FastAPI backend.
   */

  const riskScore = 22;

  const riskLevel =
    riskScore < 30
      ? "Low Risk"
      : riskScore < 60
      ? "Medium Risk"
      : "High Risk";

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
              AI has analyzed the available verification
              signals and identified the following factors.
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
              <span>Overall Risk</span>

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
              {riskLevel}
            </strong>

            <span>
              100% · Higher Risk
            </span>

          </div>

        </div>


        {/* IDENTITY */}

        <div className="ai-identity-card">

          <div className="result-avatar">
            A
          </div>

          <div>

            <span>
              Verified Identity
            </span>

            <strong>
              Sample Identity
            </strong>

            <small>
              User ID #001
            </small>

          </div>

          <div className="approved-badge">
            <CheckCircle2 size={14} />
            Verified
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
            <p>AI ASSISTANT</p>

            <h3>
              Why is the risk {riskScore}%?
            </h3>
          </div>

        </div>

        <div className="ai-explanation-text">

          <p>
            The available identity signals show a generally
            consistent identity. The face match is strong and
            the submitted documents provide supporting evidence.
          </p>

          <p>
            The risk level has increased slightly because one
            expected document is not available and the PAN
            document match is lower than the face and Aadhaar
            matches.
          </p>

        </div>

      </div>


      {/* VERIFICATION SIGNALS */}

      <div className="ai-section">

        <div className="ai-section-title">

          <div>
            <p>VERIFICATION SIGNALS</p>
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
            icon={<ScanFace size={19} />}
            name="Face Match"
            value="97%"
            status="Strong match"
            type="positive"
          />

          <AISignal
            icon={<FileCheck size={19} />}
            name="Aadhaar Match"
            value="96%"
            status="Strong match"
            type="positive"
          />

          <AISignal
            icon={<FileCheck size={19} />}
            name="PAN Match"
            value="91%"
            status="Moderate match"
            type="warning"
          />

          <AISignal
            icon={<FileCheck size={19} />}
            name="Driving Licence"
            value="Missing"
            status="Not uploaded"
            type="warning"
          />

          <AISignal
            icon={<ShieldCheck size={19} />}
            name="Identity Database"
            value="Matched"
            status="Person found in database"
            type="positive"
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
            <p>RISK FACTORS</p>

            <h3>
              Causes contributing to the risk
            </h3>
          </div>

        </div>


        <div className="risk-cause-list">

          <RiskCause
            number="01"
            title="Missing document"
            description="Driving Licence is not available in the registered document records."
          />

          <RiskCause
            number="02"
            title="Lower PAN match"
            description="The PAN verification score is lower than the face and Aadhaar match scores."
          />

          <RiskCause
            number="03"
            title="Additional verification required"
            description="The system recommends reviewing the available identity evidence before final approval."
          />

        </div>

      </div>


      {/* ADMIN RECOMMENDATION */}

      <div className="ai-review-card">

        <div className="ai-review-icon">
          <CircleAlert size={21} />
        </div>

        <div>

          <p>
            ADMIN REVIEW
          </p>

          <strong>
            Review the available identity documents
          </strong>

          <span>
            The current risk score is based on the available
            verification signals. The admin should review the
            underlying records before making a final decision.
          </span>

        </div>

      </div>


      {/* ACTION */}

      <button
        className="new-verification-button"
        onClick={onNewVerification}
      >
        <RotateCcw size={17} />
        Start New AI Verification
      </button>

    </section>
  );
}


/* -------------------------------- */
/* AI SIGNAL */
/* -------------------------------- */

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


/* -------------------------------- */
/* RISK CAUSE */
/* -------------------------------- */

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