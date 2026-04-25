"use client";
import { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { parseJD, startPipeline, startPipelineWithFiles } from "@/lib/api";
import {
  Rocket, FileText, Download, Target, MessageSquare, Trophy,
  Eye, EyeOff, CheckCircle, Inbox, Paperclip, BarChart, ClipboardList,
  Folder, X, Link as LinkIcon, Settings, AlertTriangle, Check, Loader, BookOpen
} from "lucide-react";

const SAMPLE_JD = `Senior Full-Stack Engineer — FinTech Startup (Series B)
Location: Remote (US timezone preferred) | Type: Full-time

We're looking for a Senior Full-Stack Engineer with 5+ years of experience to join our
12-person engineering team building next-generation B2B payment infrastructure.

Required: React, Node.js, PostgreSQL, AWS (ECS, RDS, S3), TypeScript, Docker.
Nice to have: GraphQL, Stripe API, Kubernetes, FinTech domain experience.

Compensation: $160k–$200k + equity. Start date: ASAP.`;

const CSV_SAMPLE = `id,name,skills,experience_years,location,email,education
cand_001,Alice Johnson,"React,Node.js,PostgreSQL,AWS,TypeScript",6,Remote,alice@email.com,Bachelor's CS
cand_002,Bob Chen,"Python,FastAPI,Docker,Kubernetes",8,San Francisco CA,bob@email.com,Master's SE
cand_003,Priya Nair,"React,TypeScript,GraphQL,Node.js",5,Remote,priya@email.com,Bachelor's CS`;

const CSV_COLS = [
  { name: "id", req: false, desc: "Auto-generated if blank" },
  { name: "name", req: true, desc: "Full name" },
  { name: "skills", req: true, desc: 'Comma-separated, quoted e.g. "React,Node.js"' },
  { name: "experience_years", req: true, desc: "Number e.g. 5 or 5.5" },
  { name: "location", req: false, desc: "City State or Remote" },
  { name: "email", req: false, desc: "Used for deduplication" },
  { name: "education", req: false, desc: "e.g. Bachelor's Computer Science" },
];

type FileEntry = { file: File; kind: "resume" | "csv" | "json" };

const PIPELINE_STEPS = [
  { icon: FileText, label: "Parse JD" },
  { icon: Inbox, label: "Ingest" },
  { icon: Target, label: "Match" },
  { icon: MessageSquare, label: "Converse" },
  { icon: Trophy, label: "Rank" }
];

export default function LaunchpadPage() {
  const router = useRouter();
  const resumeRef = useRef<HTMLInputElement>(null);
  const csvRef = useRef<HTMLInputElement>(null);

  const [jd, setJd] = useState("");
  const [urls, setUrls] = useState("");
  const [useDefault, setDef] = useState(true);
  const [useResumes, setUseResumes] = useState(false);
  const [useData, setUseData] = useState(false);
  const [useUrls, setUseUrls] = useState(false);
  const [topN, setTopN] = useState(10);
  const [wMatch, setWMatch] = useState(60);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [dragResume, setDragR] = useState(false);
  const [dragCsv, setDragC] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [provider, setProvider] = useState<"gemini" | "openrouter">("openrouter");
  const [openrouterModel, setOpenrouterModel] = useState("google/gemma-3-27b-it:free");
  const [geminiKey, setGeminiKey] = useState("");
  const [openrouterKey, setOpenrouterKey] = useState("");
  const [useOwnKey, setUseOwnKey] = useState(false);
  const [showCsv, setShowCsv] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const savedGemini = localStorage.getItem("GEMINI_API_KEY") || "";
    const savedOR = localStorage.getItem("OPENROUTER_API_KEY") || "";
    const savedORM = localStorage.getItem("OPENROUTER_MODEL") || "google/gemma-3-27b-it:free";
    const savedProvider = (localStorage.getItem("LLM_PROVIDER") as "gemini" | "openrouter") || "gemini";
    const savedUseOwn = localStorage.getItem("USE_OWN_KEY") === "true";

    setGeminiKey(savedGemini);
    setOpenrouterKey(savedOR);
    setOpenrouterModel(savedORM);
    setProvider(savedProvider);
    setUseOwnKey(savedUseOwn);
  }, []);

  const handleToggleOwnKey = (val: boolean) => {
    setUseOwnKey(val);
    localStorage.setItem("USE_OWN_KEY", val.toString());
  };

  const handleSaveGemini = (key: string) => {
    setGeminiKey(key);
    localStorage.setItem("GEMINI_API_KEY", key);
  };

  const handleSaveOR = (key: string) => {
    setOpenrouterKey(key);
    localStorage.setItem("OPENROUTER_API_KEY", key);
  };

  const handleSetProvider = (p: "gemini" | "openrouter") => {
    setProvider(p);
    localStorage.setItem("LLM_PROVIDER", p);
  };

  const handleSetORModel = (m: string) => {
    setOpenrouterModel(m);
    localStorage.setItem("OPENROUTER_MODEL", m);
  };

  const currentKey = provider === "gemini" ? geminiKey : openrouterKey;
  const isKeyActive = currentKey.length > 20;

  const addFiles = (list: FileList | null, zone: "resume" | "csv") => {
    if (!list) return;
    setFiles(prev => {
      const next = [...prev];
      Array.from(list).forEach(f => {
        if (next.find(e => e.file.name === f.name)) return;
        const n = f.name.toLowerCase();
        const kind: FileEntry["kind"] = n.endsWith(".csv") ? "csv" : n.endsWith(".json") ? "json" : "resume";
        next.push({ file: f, kind });
      });
      return next;
    });
  };


  const total = (useDefault ? 1 : 0) + (useResumes ? 1 : 0) + (useData ? 1 : 0) + (useUrls ? 1 : 0);

  const handleLaunch = async () => {
    if (!jd.trim()) { setError("Paste a job description first."); return; }
    if (total === 0) { setError("Add at least one candidate source."); return; }
    setLoading(true); setError("");
    const jobId = `job_${Date.now()}`;
    const urlList = useUrls ? urls.split("\n").map(u => u.trim()).filter(Boolean) : [];
    const activeFiles = files.filter(f => (useResumes && f.kind === "resume") || (useData && (f.kind === "csv" || f.kind === "json")));

    const effectiveModel = provider === "gemini" ? "gemini-2.5-flash-lite" : openrouterModel;
    try {
      if (activeFiles.length > 0) {
        await startPipelineWithFiles({ jobId, jdText: jd, files: activeFiles.map(e => e.file), candidateUrls: urlList, useDefaultDataset: useDefault, topN, wMatch: wMatch / 100, wInterest: (100 - wMatch) / 100, provider, model: effectiveModel });
      } else {
        await startPipeline({ jobId, jdText: jd, candidateUrls: urlList, useDefaultDataset: useDefault, topN, wMatch: wMatch / 100, wInterest: (100 - wMatch) / 100, provider, model: effectiveModel });
      }
      router.push(`/pipeline?jobId=${jobId}&role=Scouting%20Session`);
    } catch (e: any) { setError(e.message || "Failed to start"); setLoading(false); }
  };

  return (
    <>
      <div className="topbar">
        <span><Rocket size={18} className="text-blue" /></span>
        <span className="topbar-title">Launchpad</span>
        <span className="topbar-sub">Configure &amp; Launch Pipeline</span>
        {total > 0 && (
          <span className="chip chip-green" style={{ marginLeft: "auto" }}>
            {total} source{total > 1 ? "s" : ""} ready
          </span>
        )}
      </div>

      <div className="page">
        <div style={{ marginBottom: 32, paddingBottom: 24, borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 20 }}>
          <div>
            <h1 style={{ fontSize: "clamp(1.6rem, 4vw, 2.2rem)", fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.15, marginBottom: 12 }}>
              AI-Powered Talent Scouting<br />
              <span style={{ color: "var(--blue)" }}>&amp; Engagement Agent</span>
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", maxWidth: 540 }}>
              Paste a JD, add candidate sources, and watch the 4-stage Gemini pipeline match, converse, and rank candidates in minutes.
            </p>
            <div style={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 4, marginTop: 20 }}>
              {PIPELINE_STEPS.map((step, i, arr) => (
                <div key={step.label} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                  <div className="chip chip-dim" style={{ padding: "6px 14px", border: "1px solid var(--border-strong)", fontSize: "11px", color: "var(--text-secondary)" }}>
                    <step.icon size={12} /> {step.label}
                  </div>
                  {i < arr.length - 1 && (
                    <div style={{ height: 1, width: 12, background: "var(--border-strong)", flexShrink: 0 }} />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: 8 }}>
            <button className="btn btn-outline" onClick={() => router.push("/guide")}>
              <BookOpen size={16} /> How to Use Dashboard
            </button>
          </div>
        </div>

        <div className="grid-2col">
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div className="card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8, marginBottom: 16 }}>
                <div>
                  <div className="card-title" style={{ marginBottom: 4 }}>
                    <FileText size={14} /> Job Description
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", maxWidth: 380, lineHeight: 1.5 }}>
                    Gemini will automatically parse required skills, seniority, and metadata to calibrate candidate searches.
                  </div>
                </div>
                <button className="btn btn-outline btn-sm btn-blue-glow" onClick={() => setJd(SAMPLE_JD)}>
                  Use sample JD
                </button>
              </div>
              <textarea
                className="input"
                rows={11}
                placeholder="Paste your full job description here — role, required skills, experience, location, compensation..."
                value={jd}
                onChange={e => setJd(e.target.value)}
              />
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 10, flexWrap: "wrap", gap: 8 }}>
                <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
                  {jd.length.toLocaleString()} chars
                </span>
              </div>
            </div>

          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ borderBottom: "2px solid var(--border)", paddingBottom: 10 }}>
              <h2 style={{ fontSize: "0.9rem", fontWeight: 800, letterSpacing: "-0.01em", display: "flex", alignItems: "center", gap: 6 }}>
                <Inbox size={16} /> Candidate Sources
              </h2>
              <div className="card" style={{ marginBottom: 20 }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                  <h3 className="card-title">LLM Configuration</h3>
                  {isKeyActive && (
                    <span className="chip chip-green" style={{ textTransform: "uppercase", fontSize: 10, letterSpacing: "0.05em" }}>
                      Active
                    </span>
                  )}
                </div>

                <div style={{
                  background: "rgba(80, 143, 248, 0.05)",
                  border: "1px solid rgba(80, 143, 248, 0.2)",
                  borderRadius: "var(--radius-sm)",
                  padding: "8px 12px",
                  marginBottom: 16,
                  fontSize: "0.75rem",
                  color: "var(--blue)",
                  display: "flex",
                  alignItems: "center",
                  gap: 8
                }}>
                  <Loader size={14} className="spin" />
                  <span>Note: High-capacity free models may take longer to respond. We never store your API keys.</span>
                </div>

                <div className="toggle-segment" style={{ marginBottom: 16 }}>
                  <button
                    onClick={() => handleToggleOwnKey(false)}
                    className={`toggle-segment-btn ${!useOwnKey ? "active" : ""}`}
                  >
                    DEFAULT KEY
                  </button>
                  <button
                    onClick={() => handleToggleOwnKey(true)}
                    className={`toggle-segment-btn ${useOwnKey ? "active" : ""}`}
                  >
                    OWN KEY
                  </button>
                </div>

                <div className="toggle-segment" style={{ marginBottom: 16 }}>
                  <button
                    onClick={() => handleSetProvider("gemini")}
                    className={`toggle-segment-btn ${provider === "gemini" ? "active" : ""}`}
                  >
                    GEMINI
                  </button>
                  <button
                    onClick={() => handleSetProvider("openrouter")}
                    className={`toggle-segment-btn ${provider === "openrouter" ? "active" : ""}`}
                  >
                    OPENROUTER
                  </button>
                </div>


                {provider === "openrouter" && (
                  <div style={{ marginBottom: 16 }}>
                    <label style={{ display: "block", fontSize: "10px", color: "var(--text-muted)", marginBottom: 6, fontWeight: 700 }}>FREE MODELS</label>
                    <select
                      value={openrouterModel}
                      onChange={(e) => handleSetORModel(e.target.value)}
                      style={{
                        width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)",
                        padding: "10px 12px", fontSize: "0.8rem", color: "var(--text)", cursor: "pointer"
                      }}
                    >
                      <option value="google/gemma-3-27b-it:free">Gemma 3 27B (Fast / Accurate)</option>
                      <option value="openai/gpt-oss-120b:free">GPT-OSS 120B (High Capacity)</option>
                      <option value="mistralai/mistral-7b-instruct:free">Mistral 7B (Lightweight)</option>
                    </select>
                  </div>
                )}

                {useOwnKey && (
                  <div style={{ position: "relative" }}>
                    <input
                      type={showKey ? "text" : "password"}
                      placeholder={provider === "gemini" ? "Enter Gemini API Key..." : "Enter OpenRouter API Key..."}
                      value={provider === "gemini" ? geminiKey : openrouterKey}
                      onChange={(e) => provider === "gemini" ? handleSaveGemini(e.target.value) : handleSaveOR(e.target.value)}
                      style={{
                        width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)",
                        padding: "12px 14px", fontSize: "0.85rem", color: "var(--text)", transition: "border 0.2s"
                      }}
                      onFocus={(e) => e.currentTarget.style.borderColor = "var(--blue)"}
                      onBlur={(e) => e.currentTarget.style.borderColor = "var(--border)"}
                    />
                    <button
                      onClick={() => setShowKey(!showKey)}
                      style={{
                        position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                        background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer"
                      }}
                    >
                      {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                )}
                <p style={{ marginTop: 12, fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  {provider === "gemini"
                    ? "Standard high-speed analysis via Google Cloud."
                    : "Access free models like DeepSeek or Llama 3 via OpenRouter."}
                </p>
              </div>
            </div>

            <div style={{ background: "var(--surface)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", overflow: "hidden" }}>
              <label className="toggle-row" style={{ padding: "16px 20px" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)" }}>TalentScout Network</div>
                    <span className="demo-blue-tag">DEMO DATA</span>
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: 2 }}>
                    Verified synthetic profiles for testing
                  </div>
                </div>
                <div
                  className={`toggle-switch ${useDefault ? "on" : ""}`}
                  onClick={e => { e.preventDefault(); setDef(v => !v); }}
                />
              </label>
            </div>

            <div style={{ background: "var(--surface)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", overflow: "hidden" }}>
              <label className="toggle-row" style={{ padding: "16px 20px", borderBottom: useResumes ? "1px solid var(--border)" : "none" }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 6 }}>
                    <Paperclip size={14} /> Resumes — PDF / DOCX
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: 2 }}>
                    Extract skills, experience &amp; education from raw documents
                  </div>
                </div>
                <div
                  className={`toggle-switch ${useResumes ? "on" : ""}`}
                  onClick={e => { e.preventDefault(); setUseResumes(v => !v); }}
                />
              </label>
              {useResumes && (
                <div style={{ padding: "0 20px 20px 20px", paddingTop: 16 }}>
                  <div
                    className={`drop-zone ${dragResume ? "over" : ""}`}
                    onDragOver={e => { e.preventDefault(); setDragR(true); }}
                    onDragLeave={() => setDragR(false)}
                    onDrop={e => { e.preventDefault(); setDragR(false); addFiles(e.dataTransfer.files, "resume"); }}
                    onClick={() => resumeRef.current?.click()}
                  >
                    <div style={{ color: "var(--text-muted)", marginBottom: 6 }}>
                      <FileText size={32} style={{ margin: "0 auto" }} />
                    </div>
                    <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                      Drag &amp; drop or click to browse
                    </div>
                  </div>
                  <input ref={resumeRef} type="file" accept=".pdf,.docx" multiple hidden
                    onChange={e => addFiles(e.target.files, "resume")} />
                </div>
              )}
            </div>

            <div style={{ background: "var(--surface)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", overflow: "hidden" }}>
              <label className="toggle-row" style={{ padding: "16px 20px", borderBottom: useData ? "1px solid var(--border)" : "none" }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 6 }}>
                    <BarChart size={14} /> CSV / JSON Batch
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: 2 }}>
                    Process structured candidate files in bulk
                  </div>
                </div>
                <div
                  className={`toggle-switch ${useData ? "on" : ""}`}
                  onClick={e => { e.preventDefault(); setUseData(v => !v); }}
                />
              </label>
              {useData && (
                <div style={{ padding: "0 20px 20px 20px", paddingTop: 16 }}>
                  <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 10 }}>
                    <button className="btn btn-ghost btn-sm" style={{ fontSize: "11px" }}
                      onClick={() => setShowCsv(v => !v)}>
                      {showCsv ? "Hide format" : <><ClipboardList size={14} /> Format guide</>}
                    </button>
                  </div>

                  {showCsv && (
                    <div className="fade-in-up" style={{ marginBottom: 16 }}>
                      <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "16px", marginBottom: 8 }}>
                        <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--blue)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 8, letterSpacing: "0.05em" }}>
                          COLUMN REFERENCE
                        </div>
                        {CSV_COLS.map(c => (
                          <div key={c.name} style={{ display: "flex", gap: 8, marginBottom: 4, flexWrap: "wrap" }}>
                            <code style={{
                              color: c.req ? "var(--green)" : "var(--amber)",
                              fontFamily: "'JetBrains Mono', monospace",
                              fontSize: "11px",
                              minWidth: 130,
                              flexShrink: 0,
                            }}>
                              {c.name}{c.req ? " *" : ""}
                            </code>
                            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>{c.desc}</span>
                          </div>
                        ))}
                        <div style={{ marginTop: 8, fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
                          * required &nbsp;|&nbsp; no asterisk = optional
                        </div>
                      </div>
                      <div style={{ position: "relative" }}>
                        <pre style={{
                          background: "#1a1816",
                          color: "#c8c4bc",
                          fontFamily: "'JetBrains Mono', monospace",
                          fontSize: "10px",
                          padding: "10px 12px",
                          overflowX: "auto",
                          lineHeight: 1.7,
                          margin: 0,
                          border: "1px solid #333",
                        }}>
                          {CSV_SAMPLE}
                        </pre>
                        <button className="btn btn-ghost btn-sm"
                          style={{ position: "absolute", top: 6, right: 6, fontSize: "10px", color: "#c8c4bc", background: "rgba(255,255,255,0.08)" }}
                          onClick={() => { const b = new Blob([CSV_SAMPLE], { type: "text/csv" }); const a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = "candidates.csv"; a.click(); }}>
                          <Download size={12} /> Download
                        </button>
                      </div>
                    </div>
                  )}

                  <div
                    className={`drop-zone ${dragCsv ? "over" : ""}`}
                    onDragOver={e => { e.preventDefault(); setDragC(true); }}
                    onDragLeave={() => setDragC(false)}
                    onDrop={e => { e.preventDefault(); setDragC(false); addFiles(e.dataTransfer.files, "csv"); }}
                    onClick={() => csvRef.current?.click()}
                  >
                    <div style={{ color: "var(--text-muted)", marginBottom: 4 }}>
                      <BarChart size={32} style={{ margin: "0 auto" }} />
                    </div>
                    <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)" }}>
                      Drop CSV or JSON here
                    </div>
                    <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: 2 }}>or click to browse</div>
                  </div>
                  <input ref={csvRef} type="file" accept=".csv,.json" multiple hidden
                    onChange={e => addFiles(e.target.files, "csv")} />
                </div>
              )}
            </div>

            {/* URLs */}
            <div style={{ background: "var(--surface)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", overflow: "hidden" }}>
              <label className="toggle-row" style={{ padding: "16px 20px", borderBottom: useUrls ? "1px solid var(--border)" : "none" }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 6 }}>
                    <LinkIcon size={14} /> GitHub / LinkedIn URLs
                  </div>
                  <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: 2 }}>
                    Scrape profiles directly from individual links
                  </div>
                </div>
                <div
                  className={`toggle-switch ${useUrls ? "on" : ""}`}
                  onClick={e => { e.preventDefault(); setUseUrls(v => !v); }}
                />
              </label>
              {useUrls && (
                <div style={{ padding: "0 20px 20px 20px", paddingTop: 16 }}>
                  <textarea
                    className="input"
                    rows={2}
                    placeholder={"https://github.com/username\nhttps://linkedin.com/in/name"}
                    value={urls}
                    onChange={e => setUrls(e.target.value)}
                    style={{ minHeight: 70 }}
                  />
                  <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: 4 }}>One URL per line</div>
                </div>
              )}
            </div>


            {/* File queue */}
            {files.length > 0 && (
              <div className="card fade-in-up">
                <div className="card-title">
                  <Folder size={14} /> {files.length} FILE{files.length > 1 ? "S" : ""} QUEUED
                </div>
                {files.map((e, i) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "8px 0",
                    borderBottom: i < files.length - 1 ? "1px solid var(--border)" : "none",
                  }}>
                    <span style={{ color: "var(--text-muted)" }}>
                      {e.kind === "csv" ? <BarChart size={14} /> : e.kind === "json" ? <ClipboardList size={14} /> : <FileText size={14} />}
                    </span>
                    <span style={{ flex: 1, fontSize: "12px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--text-secondary)" }}>
                      {e.file.name}
                    </span>
                    <span className={`chip chip-${e.kind === "csv" ? "green" : e.kind === "json" ? "purple" : "blue"}`} style={{ fontSize: "10px" }}>
                      {e.kind.toUpperCase()}
                    </span>
                    <span style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", flexShrink: 0 }}>
                      {(e.file.size / 1024).toFixed(1)}KB
                    </span>
                    <button
                      onClick={() => setFiles(p => p.filter((_, j) => j !== i))}
                      style={{ background: "none", border: "none", color: "var(--red)", cursor: "pointer", padding: 0, display: "flex", alignItems: "center" }}
                    ><X size={14} /></button>
                  </div>
                ))}
              </div>
            )}

            {/* Settings */}
            <div className="card">
              <div className="card-title" style={{ marginBottom: 16 }}><Settings size={14} /> Pipeline Settings</div>

              <div style={{ marginBottom: 20 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>Candidates for outreach</span>
                  <strong style={{ fontFamily: "'JetBrains Mono', monospace", color: "var(--blue)" }}>{topN}</strong>
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: 8, lineHeight: 1.4 }}>
                  Maximum limit of candidates to advance to the conversational screening phase.
                </div>
                <input type="range" min={3} max={20} value={topN} onChange={e => setTopN(Number(e.target.value))} />
              </div>

              <div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                  <span style={{ fontSize: "0.875rem", fontWeight: 600, color: "var(--text-primary)" }}>Scoring Weights</span>
                  <strong style={{ fontFamily: "'JetBrains Mono', monospace", color: "var(--text-primary)" }}>{wMatch}% / {100 - wMatch}%</strong>
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: 8, lineHeight: 1.4 }}>
                  Adjust the impact of technical skills matching versus AI conversational interest.
                </div>
                <input type="range" min={40} max={80} value={wMatch} onChange={e => setWMatch(Number(e.target.value))} />
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)", marginTop: 6, fontWeight: 600 }}>
                  <span>Technical Match</span><span>AI Conversation</span>
                </div>
              </div>
            </div>

            {/* Source summary */}
            <div style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 14px",
              background: total > 0 ? "var(--green-light)" : "var(--amber-light)",
              border: `2px solid ${total > 0 ? "var(--green-mid)" : "var(--amber-mid)"}`,
              fontSize: "12px",
              fontFamily: "'JetBrains Mono', monospace",
              color: total > 0 ? "var(--green)" : "var(--amber)",
              fontWeight: 600,
              borderRadius: "var(--radius-sm)",
            }}>
              {total === 0
                ? <><AlertTriangle size={14} /> No candidate source selected</>
                : <><Check size={14} /> {total} source{total > 1 ? "s" : ""} configured{files.length > 0 ? ` · ${files.length} file${files.length > 1 ? "s" : ""}` : ""}</>
              }
            </div>

            {/* Error */}
            {error && (
              <div style={{ display: "flex", flexDirection: "column", gap: 8, background: "var(--red-light)", border: "2px solid var(--red-mid)", padding: "10px 14px", fontSize: "0.875rem", color: "var(--red)", borderRadius: "var(--radius-sm)" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <AlertTriangle size={16} /> {error}
                </div>
                {(error.includes("429") || error.includes("Rate limit")) && (
                  <div style={{ padding: "8px", background: "rgba(80, 143, 248, 0.1)", border: "1px solid var(--blue)", borderRadius: 6, color: "var(--blue)", fontSize: "0.8rem", fontWeight: 500 }}>
                    💡 Tip: If the rate limit persists, try using your own API key in the configuration above.
                  </div>
                )}
              </div>
            )}

            {/* Launch */}
            <button
              className="btn btn-primary"
              style={{ width: "100%", justifyContent: "center", padding: "14px", fontSize: "0.95rem", letterSpacing: "0.01em" }}
              onClick={handleLaunch}
              disabled={loading || !jd.trim() || total === 0}
            >
              {loading
                ? <><Loader size={16} className="spin" />&nbsp;Initializing pipeline...</>
                : <><Rocket size={16} /> Launch Pipeline</>
              }
            </button>

            <div style={{ textAlign: "center", fontSize: "11px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>
              Gemini 2.5 Flash · 4-stage pipeline · 60s avg
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
