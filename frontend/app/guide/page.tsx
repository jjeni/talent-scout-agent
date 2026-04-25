"use client";
import { Info, HelpCircle, FileText, Database, Target, Map, ShieldCheck, Zap } from "lucide-react";

export default function GuidePage() {
  return (
    <>
      <div className="topbar">
        <HelpCircle size={18} className="text-blue" />
        <span className="topbar-title">Features & User Guide</span>
        <span className="topbar-sub">Documentation</span>
      </div>

      <div className="page fade-in-up" style={{ maxWidth: 1000, margin: "0 auto", paddingBottom: 64 }}>
        <div style={{ marginBottom: 48 }}>
        <h1 style={{ fontSize: "2rem", fontWeight: 700, marginBottom: 16 }}>Welcome to TalentScout AI</h1>
        <p style={{ color: "var(--text-secondary)", fontSize: "1.05rem", maxWidth: 680, lineHeight: 1.6 }}>
          TalentScout is a next-generation recruitment platform powered by Google Gemini. It automates candidate sourcing, parsing, matching, and multi-stage conversational screening — drastically reducing your time-to-hire.
        </p>
      </div>

      <div className="grid-2col-even" style={{ marginBottom: 48 }}>
        {/* Features - AI Core */}
        <div className="card" style={{ padding: "28px" }}>
          <div className="card-title" style={{ color: "var(--blue)", marginBottom: 16 }}>
            <Zap size={14} /> Core Capabilities
          </div>
          <ul style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <li style={{ display: "flex", gap: 12 }}>
              <div style={{ padding: 8, background: "var(--blue-light)", color: "var(--blue)", borderRadius: "var(--radius-sm)", height: "fit-content" }}>
                <FileText size={18} />
              </div>
              <div>
                <strong style={{ display: "block", marginBottom: 4 }}>Intelligent JD Parsing</strong>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.5, display: "block" }}>
                  Simply paste a job description. Gemini handles extracting roles, defining seniority, mapping skill prerequisites, and creating search context.
                </span>
              </div>
            </li>
            <li style={{ display: "flex", gap: 12 }}>
              <div style={{ padding: 8, background: "var(--green-light)", color: "var(--green)", borderRadius: "var(--radius-sm)", height: "fit-content" }}>
                <Target size={18} />
              </div>
              <div>
                <strong style={{ display: "block", marginBottom: 4 }}>Multi-modal Sourcing</strong>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.5, display: "block" }}>
                  Ingest profiles from LinkedIn URLs, direct resume uploads (PDF/Docx), or structural batch data via CSV pipelines directly to our vector database.
                </span>
              </div>
            </li>
            <li style={{ display: "flex", gap: 12 }}>
              <div style={{ padding: 8, background: "var(--purple-light)", color: "var(--purple)", borderRadius: "var(--radius-sm)", height: "fit-content" }}>
                <ShieldCheck size={18} />
              </div>
              <div>
                <strong style={{ display: "block", marginBottom: 4 }}>Semantic Matching Engine</strong>
                <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.5, display: "block" }}>
                  Go beyond keyword matching. TalentScout scores applicants based on structural alignment to your JD utilizing RAG & vector embeddings.
                </span>
              </div>
            </li>
          </ul>
        </div>

        {/* How to use */}
        <div className="card" style={{ padding: "28px" }}>
          <div className="card-title" style={{ color: "var(--amber)", marginBottom: 16 }}>
            <Map size={14} /> How To Use Launchpad
          </div>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ padding: 16, background: "var(--surface-high)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-strong)" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--amber)", marginBottom: 6 }}>Step 1: Paste JD</div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0 }}>
                Copy and paste the full Job Description into the text area. Alternatively, click "Use sample JD" to run a quick test.
              </p>
            </div>

            <div style={{ padding: 16, background: "var(--surface-high)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-strong)" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--amber)", marginBottom: 6 }}>Step 2: Connect Sources</div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0 }}>
                Toggle exactly where you want to find candidates. You can drag and drop multiple PDF resumes, upload a curated CSV, or link to profiles.
              </p>
            </div>

            <div style={{ padding: 16, background: "var(--surface-high)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-strong)" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--amber)", marginBottom: 6 }}>Step 3: Tune Settings & Launch</div>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", margin: 0 }}>
                Adjust your screening limits and weighting. Hit "Launch Pipeline" and the agent takes over everything from parsing to scoring.
              </p>
            </div>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: "1.4rem", fontWeight: 600, marginBottom: 20 }}>Frequently Asked Questions</h2>
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        
        <div style={{ padding: 24, borderBottom: "1px solid var(--border)" }}>
          <strong style={{ display: "block", marginBottom: 8, fontSize: "1rem" }}>How does conversational AI screening work?</strong>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6, margin: 0 }}>
            Once the top matching candidates are shortlisted by the vector engine, the system automatically engages them in simulated outreach parsing, gauging their level of interest, salary overlap, and soft skills before presenting you the final ranked shortlist.
          </p>
        </div>

        <div style={{ padding: 24, borderBottom: "1px solid var(--border)" }}>
          <strong style={{ display: "block", marginBottom: 8, fontSize: "1rem" }}>What happens to uploaded resumes?</strong>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6, margin: 0 }}>
            PDF resumes are chunked and embedded via Gemini 2.5 context window. They are ephemeral files during processing and are immediately reduced into normalized JSON profiles for privacy compliance.
          </p>
        </div>

        <div style={{ padding: 24, borderBottom: "1px solid var(--border)" }}>
          <strong style={{ display: "block", marginBottom: 8, fontSize: "1rem" }}>Are my API keys stored on your servers?</strong>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6, margin: 0 }}>
            Absolutely not. TalentScout AI follows a "Zero Persistence" policy for client credentials. All API keys (Gemini, OpenRouter, etc.) are stored strictly in your browser's local storage and used only for direct backend requests. We never log, save, or track your personal keys.
          </p>
        </div>

        <div style={{ padding: 24 }}>
          <strong style={{ display: "block", marginBottom: 8, fontSize: "1rem" }}>Can I export the Shortlist?</strong>
          <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", lineHeight: 1.6, margin: 0 }}>
            Yes, on the Shortlist screen, you'll see a CSV Export button to download all scored candidates, their match metadata, and AI rationale to import into your company's ATS.
          </p>
        </div>
      </div>
    </div>
    </>
  );
}
