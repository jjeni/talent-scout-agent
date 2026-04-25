"use client";
import { useEffect, useRef, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { subscribePipelineStatus as subscribeToProgress } from "@/lib/api";
import { FileText, Inbox, Target, MessageSquare, Trophy, Check, X, Loader, Settings, PartyPopper, AlertTriangle } from "lucide-react";

const STAGES = [
  { key: "parsing_jd", icon: FileText, label: "Parse JD" },
  { key: "ingesting",  icon: Inbox,    label: "Ingest"   },
  { key: "matching",   icon: Target,     label: "Match"    },
  { key: "conversing", icon: MessageSquare, label: "Converse" },
  { key: "ranking",    icon: Trophy,    label: "Rank"     },
];

type LogEntry = { ts: string; pct: number; msg: string; kind: "info" | "success" | "warn" };

function PipelineInner() {
  const router   = useRouter();
  const params   = useSearchParams();
  const jobId    = params.get("jobId") || "";
  const role     = params.get("role") || "Pipeline";
  const logRef   = useRef<HTMLDivElement>(null);

  const [stage, setStage]       = useState("");
  const [progress, setProgress] = useState(0);
  const [message, setMessage]   = useState("Initializing pipeline...");
  const [candidate, setCand]    = useState("");
  const [done, setDone]         = useState(false);
  const [errMsg, setErr]        = useState("");
  const [logs, setLogs]         = useState<LogEntry[]>([]);
  const [elapsed, setElapsed]   = useState(0);
  const [startTime]             = useState(Date.now());

  useEffect(() => {
    if (done || errMsg) return;
    const t = setInterval(() => setElapsed(Math.floor((Date.now() - startTime) / 1000)), 1000);
    return () => clearInterval(t);
  }, [done, errMsg, startTime]);

  useEffect(() => {
    if (!jobId) return;
    const unsub = subscribeToProgress(
      jobId,
      (data: any) => {
        setStage(data.stage || "");
        setProgress(data.progress || 0);
        setMessage(data.message || "");
        setCand(data.current_candidate || "");
        const ts = new Date().toLocaleTimeString("en-US", { hour12: false });
        const kind: LogEntry["kind"] = data.stage === "error" ? "warn" : "info";
        setLogs(prev => [...prev, { ts, pct: data.progress || 0, msg: data.message || "", kind }]);
      },
      () => {
        setDone(true);
        setLogs(prev => {
          const ts = new Date().toLocaleTimeString("en-US", { hour12: false });
          return [...prev, { ts, pct: 100, msg: "Pipeline complete. Redirecting to results...", kind: "success" }];
        });
        setTimeout(() => router.push(`/shortlist?jobId=${jobId}&role=${encodeURIComponent(role)}`), 2000);
      },
      (err: string) => setErr(err)
    );
    return unsub;
  }, [jobId, role, router]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [logs]);

  const stageIdx = (() => {
    if (stage === "done")  return STAGES.length;
    if (stage === "error") return -1;
    return STAGES.findIndex(s => s.key === stage);
  })();

  const getState = (i: number) => {
    if (stageIdx < 0)   return "pending";
    if (i < stageIdx)   return "done";
    if (i === stageIdx) return "active";
    return "pending";
  };

  const fmt = (s: number) =>
    `${String(Math.floor(s / 60)).padStart(2,"0")}:${String(s % 60).padStart(2,"0")}`;

  return (
    <>
      <div className="topbar">
        {done ? <span><Check size={18} className="text-green" /></span> : errMsg ? <span><X size={18} className="text-red" /></span> : <span><Loader size={18} className="spin text-blue" /></span>}
        <span className="topbar-title">Pipeline: {role}</span>
        <span className="topbar-sub" style={{ maxWidth: 200, overflow: "hidden", textOverflow: "ellipsis" }}>
          {jobId}
        </span>
        <span style={{ marginLeft: "auto", fontFamily: "'JetBrains Mono', monospace", fontSize: "12px", fontWeight: 700, color: "var(--blue)" }}>
          {fmt(elapsed)}
        </span>
      </div>

      <div className="page" style={{ maxWidth: 840 }}>

        {/* Stage tracker */}
        <div className="card" style={{ marginBottom: 16, padding: "18px 20px" }}>
          <div className="card-title">EXECUTION STAGES</div>
          <div className="stage-track">
            {STAGES.map((s, i) => {
              const st = getState(i);
              return (
                <div key={s.key} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                  <div className="stage-item">
                    <div className={`stage-dot ${st}`}>
                      {st === "done" ? <Check size={16} /> : <s.icon size={16} />}
                    </div>
                    <div className={`stage-label ${st}`}>{s.label}</div>
                  </div>
                  {i < STAGES.length - 1 && (
                    <div className={`stage-line ${st === "done" ? "done" : st === "active" ? "active" : ""}`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Progress bar */}
        <div className="card" style={{ marginBottom: 16, padding: "18px 20px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
            <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", flex: 1, paddingRight: 12 }}>
              {message}
            </span>
            <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "1.4rem", fontWeight: 700, color: "var(--blue)", flexShrink: 0 }}>
              {progress}%
            </span>
          </div>
          <div className="progress-track">
            <div className="progress-fill" style={{ width: `${progress}%` }} />
          </div>
        </div>

        {/* Current candidate */}
        {candidate && !done && !errMsg && (
          <div className="card fade-in-up" style={{
            marginBottom: 16,
            padding: "14px 18px",
            borderColor: "var(--blue)",
            borderLeftWidth: 4,
            background: "var(--blue-light)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span><Settings size={20} className="spin text-blue" /></span>
              <div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 2 }}>
                  ANALYZING PROFILE
                </div>
                <div style={{ fontWeight: 700, color: "var(--blue)", fontSize: "0.95rem" }}>{candidate}</div>
              </div>
            </div>
          </div>
        )}

        {/* Done card */}
        {done && (
          <div className="card fade-in-up" style={{
            marginBottom: 16,
            padding: "28px 24px",
            background: "var(--green-light)",
            borderColor: "var(--green-mid)",
            borderLeftWidth: 4,
            textAlign: "center",
          }}>
            <div style={{ marginBottom: 10, display: "flex", justifyContent: "center", color: "var(--green)" }}>
              <PartyPopper size={48} />
            </div>
            <div style={{ fontWeight: 800, fontSize: "1.1rem", color: "var(--green)", marginBottom: 6 }}>
              Pipeline Complete!
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
              Redirecting to results<span className="blink">...</span>
            </div>
          </div>
        )}

        {/* Error card */}
        {errMsg && (
          <div className="card fade-in-up" style={{
            marginBottom: 16,
            padding: "18px 20px",
            background: "var(--red-light)",
            borderColor: "var(--red-mid)",
            borderLeftWidth: 4,
          }}>
            <div style={{ fontWeight: 700, color: "var(--red)", marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
              <AlertTriangle size={16} /> Pipeline Error
            </div>
            <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontFamily: "'JetBrains Mono', monospace", whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
              {errMsg}
            </div>
            <button className="btn btn-outline btn-sm" style={{ marginTop: 14 }} onClick={() => router.push("/")}>
              ← Return to Launchpad
            </button>
          </div>
        )}

        {/* Activity log */}
        <div className="terminal">
          <div className="terminal-header">
            <div className="terminal-dot" style={{ background: "#ff5f57" }} />
            <div className="terminal-dot" style={{ background: "#febc2e" }} />
            <div className="terminal-dot" style={{ background: "#28c840" }} />
            <span style={{ marginLeft: 8, fontSize: "11px", fontFamily: "'JetBrains Mono', monospace", color: "#6b7280" }}>
              Live Activity Feed
            </span>
            <span style={{ marginLeft: "auto", fontSize: "11px", fontFamily: "'JetBrains Mono', monospace", color: "#6b7280" }}>
              {logs.length} events
            </span>
          </div>
          <div className="terminal-body" ref={logRef}>
            {logs.length === 0 && (
              <div className="log-line">
                <span className="log-time">00:00:00</span>
                <span className="log-pct">0%</span>
                <span className="log-msg">Waiting for pipeline events<span className="blink">_</span></span>
              </div>
            )}
            {logs.map((l, i) => (
              <div key={i} className="log-line">
                <span className="log-time">{l.ts}</span>
                <span className="log-pct">{l.pct}%</span>
                <span className={`log-msg ${l.kind}`}>{l.msg}</span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 20, display: "flex", justifyContent: "center" }}>
          <button className="btn btn-ghost btn-sm" onClick={() => router.push("/")}>
            ← Back to Launchpad
          </button>
        </div>
      </div>
    </>
  );
}

export default function PipelinePage() {
  return (
    <Suspense fallback={
      <div style={{ padding: 32, fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)" }}>
        Loading pipeline...
      </div>
    }>
      <PipelineInner />
    </Suspense>
  );
}
