"use client";
import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getShortlist } from "@/lib/api";
import { 
  Trophy, Users, CheckCircle, Target, MessageSquare, Timer, 
  Eye, AlertTriangle, X, ChevronDown, ChevronUp, Bot, User 
} from "lucide-react";

type RankedEntry = {
  rank: number;
  candidate_name: string;
  candidate_id: string;
  match_score: number;
  interest_score: number;
  combined_score: number;
  top_match_reasons: string[];
  interest_summary: string;
  recruiter_note: string;
  source_type: string;
  strengths?: string[];
  gaps?: string[];
  key_signals?: string[];
  red_flags?: string[];
};
type Turn = { speaker: string; message: string };
type ScoredCandidate = {
  profile: { id: string; name: string };
  transcript?: { turns: Turn[] };
};
type ShortlistOutput = {
  ranked_candidates: RankedEntry[];
  job_id: string;
  role_title: string;
  excluded: Array<{ name: string; reason: string }>;
  candidates: ScoredCandidate[];
  processing_time_seconds: number;
  total_evaluated: number;
};

function scoreClass(s: number) {
  if (s >= 80) return "green";
  if (s >= 60) return "blue";
  if (s >= 40) return "amber";
  return "red";
}

function Medal({ rank }: { rank: number }) {
  const cls = rank === 1 ? "rank-gold" : rank === 2 ? "rank-silver" : rank === 3 ? "rank-bronze" : "rank-plain";
  return (
    <div className={`rank-medal ${cls}`}>
       {rank === 1 ? <Trophy size={14} className="text-yellow-600" /> : rank === 2 ? <Trophy size={14} className="text-gray-400" /> : rank === 3 ? <Trophy size={14} className="text-orange-600" /> : rank}
    </div>
  );
}

function ScoreBox({ value }: { value: number }) {
  return <div className={`score-box ${scoreClass(value)}`}>{value.toFixed(0)}</div>;
}

function ShortlistInner() {
  const router = useRouter();
  const params = useSearchParams();
  const jobId  = params.get("jobId") || "";
  const role   = params.get("role") || "Shortlist";

  const [data, setData]             = useState<ShortlistOutput | null>(null);
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState("");
  const [sortBy, setSortBy]         = useState<"combined_score"|"match_score"|"interest_score">("combined_score");
  const [modal, setModal]           = useState<RankedEntry | null>(null);
  const [showExcluded, setExcluded] = useState(false);
  const [transcripts, setTranscripts] = useState<Record<string, Turn[]>>({});
  const [isMobile, setIsMobile]     = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 700);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    if (!jobId) return;
    let attempts = 0;
    const tryFetch = async () => {
      try {
        const result: any = await getShortlist(jobId);
        setData(result);
        const tMap: Record<string, Turn[]> = {};
        result.candidates?.forEach((c: ScoredCandidate) => {
          if (c.transcript?.turns) tMap[c.profile.id] = c.transcript.turns;
        });
        setTranscripts(tMap);
        setLoading(false);
      } catch {
        if (attempts++ < 30) setTimeout(tryFetch, 3000);
        else { setError("Timed out waiting for results."); setLoading(false); }
      }
    };
    tryFetch();
  }, [jobId]);

  const sorted = data
    ? [...data.ranked_candidates].sort((a, b) => b[sortBy] - a[sortBy])
    : [];

  const avg = (key: keyof RankedEntry) =>
    sorted.length ? (sorted.reduce((s, c) => s + (c[key] as number), 0) / sorted.length).toFixed(0) : "—";

  if (loading) return (
    <>
      <div className="topbar"><span className="topbar-title">Loading results...</span></div>
      <div className="page">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="card" style={{ height: 76, marginBottom: 2, opacity: 0.25 + i * 0.15, background: "var(--surface-high)" }} />
        ))}
      </div>
    </>
  );

  if (error) return (
    <>
      <div className="topbar"><span className="topbar-title">Error</span></div>
      <div className="page">
        <div className="card" style={{ background: "var(--red-light)", borderColor: "var(--red-mid)", borderLeftWidth: 4, padding: 24 }}>
          <div style={{ fontWeight: 700, color: "var(--red)", marginBottom: 8, display: "flex", alignItems: "center", gap: 8 }}>
            <AlertTriangle size={16} /> {error}
          </div>
          <button className="btn btn-outline btn-sm" onClick={() => router.push("/")}>← Back to Launchpad</button>
        </div>
      </div>
    </>
  );

  if (!data) return null;

  return (
    <>
      <div className="topbar">
        <span><Trophy size={18} className="text-yellow-500" /></span>
        <span className="topbar-title">Command Center</span>
        <span className="topbar-sub">{role}</span>
        <button className="btn btn-ghost btn-sm" style={{ marginLeft: "auto" }} onClick={() => router.push("/")}>
          ← New Pipeline
        </button>
      </div>

      <div className="page" style={{ maxWidth: "100%" }}>

        {/* Header */}
        <div style={{ marginBottom: 20, paddingBottom: 16, borderBottom: "2px solid var(--border)" }}>
          <h1 style={{ fontSize: "clamp(1.2rem, 3vw, 1.6rem)", fontWeight: 800, letterSpacing: "-0.02em", marginBottom: 6 }}>
            Ranked Shortlist
            <span style={{ color: "var(--blue)", marginLeft: 10 }}>Top {sorted.length}</span>
          </h1>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)" }}>
            AI evaluated{" "}
            <strong style={{ color: "var(--text-primary)" }}>{data.total_evaluated || sorted.length}</strong>{" "}
            candidates · Showing highest alignment matches
          </p>
        </div>

        {/* Stats row */}
        <div className="stat-grid" style={{ marginBottom: 20, gap: 0 }}>
          {[
            { icon: Users, label: "EVALUATED",   value: data.total_evaluated || sorted.length },
            { icon: CheckCircle, label: "SHORTLISTED", value: sorted.length },
            { icon: Target, label: "AVG MATCH",   value: avg("match_score") },
            { icon: MessageSquare, label: "AVG INTEREST",value: avg("interest_score") },
            { icon: Timer,  label: "RUNTIME",     value: `${(data.processing_time_seconds || 0).toFixed(0)}s` },
          ].map((s, i) => (
            <div key={s.label} className="stat-card">
              <div style={{ marginBottom: 6, color: "var(--text-secondary)" }}><s.icon size={20} /></div>
              <div className="stat-value">{s.value}</div>
              <div className="stat-label">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Sort controls */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "var(--text-muted)", fontWeight: 600, letterSpacing: "0.08em", textTransform: "uppercase" }}>
            Sort by:
          </div>
          <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
            {(["combined_score","match_score","interest_score"] as const).map(k => (
              <button key={k}
                className={`btn btn-sm ${sortBy === k ? "btn-primary" : "btn-outline"}`}
                style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: 4 }}
                onClick={() => setSortBy(k)}>
                {k === "combined_score" ? <><Trophy size={12}/> Combined</> : k === "match_score" ? <><Target size={12}/> Match</> : <><MessageSquare size={12}/> Interest</>}
              </button>
            ))}
          </div>
        </div>

        {/* Desktop table */}
        {!isMobile ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: 48 }}>#</th>
                  <th>Candidate</th>
                  <th>Source</th>
                  <th>Match</th>
                  <th>Interest</th>
                  <th>Combined</th>
                  <th>Top Reasons</th>
                  <th>Recruiter Note</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((c, i) => (
                  <tr key={c.candidate_id}>
                    <td><Medal rank={i + 1} /></td>
                    <td>
                      <div style={{ fontWeight: 700 }}>{c.candidate_name}</div>
                    </td>
                    <td>
                      <span className={`chip chip-${c.source_type === "github" ? "purple" : c.source_type === "pdf" || c.source_type === "docx" ? "blue" : "dim"}`}>
                        {(c.source_type || "N/A").toUpperCase()}
                      </span>
                    </td>
                    <td><ScoreBox value={c.match_score} /></td>
                    <td><ScoreBox value={c.interest_score} /></td>
                    <td>
                      <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "1.3rem", fontWeight: 800, color: "var(--blue)" }}>
                        {c.combined_score.toFixed(0)}
                      </div>
                    </td>
                    <td style={{ maxWidth: 200 }}>
                      <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
                        {c.top_match_reasons?.slice(0, 2).map((r, j) => (
                          <div key={j} style={{ fontSize: "11px", color: "var(--text-muted)", display: "flex", alignItems: "flex-start", gap: 5 }}>
                            <span style={{ color: "var(--green)", flexShrink: 0 }}>▸</span>
                            <span>{r}</span>
                          </div>
                        ))}
                      </div>
                    </td>
                    <td style={{ maxWidth: 200 }}>
                      <div style={{ fontSize: "11px", color: "var(--text-muted)", fontStyle: "italic", lineHeight: 1.45 }}>
                        {c.recruiter_note}
                      </div>
                    </td>
                    <td>
                      <button className="btn btn-outline btn-sm" style={{ fontSize: "11px", whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 4 }}
                        onClick={() => setModal(c)}>
                        <Eye size={12} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          /* Mobile card list */
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {sorted.map((c, i) => (
              <div key={c.candidate_id} className="card">
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                  <Medal rank={i + 1} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: "0.95rem" }}>{c.candidate_name}</div>
                    <div style={{ marginTop: 3 }}>
                      <span className={`chip chip-${c.source_type === "github" ? "purple" : "dim"}`}>
                        {(c.source_type || "N/A").toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "1.6rem", fontWeight: 800, color: "var(--blue)", lineHeight: 1 }}>
                      {c.combined_score.toFixed(0)}
                    </div>
                    <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace" }}>COMBINED</div>
                  </div>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 10 }}>
                  <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "12px" }}>
                    <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 2 }}>MATCH</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: "1.1rem", color: `var(--${scoreClass(c.match_score)})` }}>
                      {c.match_score.toFixed(0)}
                    </div>
                  </div>
                  <div style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "var(--radius-sm)", padding: "12px" }}>
                    <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 2 }}>INTEREST</div>
                    <div style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: "1.1rem", color: `var(--${scoreClass(c.interest_score)})` }}>
                      {c.interest_score.toFixed(0)}
                    </div>
                  </div>
                </div>
                {c.top_match_reasons?.slice(0, 1).map((r, j) => (
                  <div key={j} style={{ fontSize: "11px", color: "var(--text-muted)", marginBottom: 6, display: "flex", gap: 5 }}>
                    <span style={{ color: "var(--green)" }}>▸</span>{r}
                  </div>
                ))}
                <button className="btn btn-outline btn-sm" style={{ width: "100%", justifyContent: "center", display: "flex", alignItems: "center", gap: 4 }}
                  onClick={() => setModal(c)}>
                  <Eye size={12} /> View Transcript
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Excluded section */}
        {data.excluded?.length > 0 && (
          <div style={{ marginTop: 24 }}>
            <button className="btn btn-ghost btn-sm" onClick={() => setExcluded(v => !v)}
              style={{ fontSize: "12px", color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 4 }}>
              <AlertTriangle size={12} className="text-red-500" /> {data.excluded.length} candidates excluded {showExcluded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
            </button>
            {showExcluded && (
              <div className="card fade-in-up" style={{ marginTop: 10 }}>
                <div className="card-title">EXCLUDED CANDIDATES</div>
                {data.excluded.map((e, i) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "flex-start", gap: 12, padding: "8px 0",
                    borderBottom: i < data.excluded.length - 1 ? "1px solid var(--border)" : "none",
                    flexWrap: "wrap",
                  }}>
                    <span style={{ color: "var(--red)", flexShrink: 0 }}><X size={14} /></span>
                    <span style={{ fontWeight: 600, fontSize: "0.875rem", minWidth: 140 }}>{e.name}</span>
                    <span style={{ color: "var(--text-muted)", fontSize: "12px", fontFamily: "'JetBrains Mono', monospace" }}>{e.reason}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Modal */}
      {modal && (
        <div className="modal-backdrop" onClick={() => setModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 800, fontSize: "1rem", marginBottom: 8 }}>{modal.candidate_name}</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                  <span className={`chip chip-${scoreClass(modal.match_score)}`} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <Target size={12}/> Match {modal.match_score.toFixed(0)}
                  </span>
                  <span className={`chip chip-${scoreClass(modal.interest_score)}`} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <MessageSquare size={12}/> Interest {modal.interest_score.toFixed(0)}
                  </span>
                  <span className="chip chip-blue" style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <Trophy size={12}/> Combined {modal.combined_score.toFixed(0)}
                  </span>
                </div>
              </div>
              <button className="btn btn-ghost btn-icon" onClick={() => setModal(null)}
                style={{ fontSize: "1.2rem", color: "var(--text-muted)", flexShrink: 0 }}><X size={16} /></button>
            </div>
            <div className="modal-body">

              {/* Interest summary */}
              {modal.interest_summary && (
                <div style={{
                  background: "var(--green-light)",
                  border: "1.5px solid var(--green-mid)",
                  borderLeftWidth: 3,
                  borderLeftColor: "var(--green)",
                  padding: "12px 14px",
                  marginBottom: 16,
                }}>
                  <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--green)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 4, letterSpacing: "0.08em" }}>
                    AI INTEREST ANALYSIS
                  </div>
                  <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                    {modal.interest_summary}
                  </div>

                  {/* Conversation Signals (Key Signals & Red Flags) */}
                  {( (modal.key_signals && modal.key_signals.length > 0) || (modal.red_flags && modal.red_flags.length > 0) ) && (
                    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
                      {modal.key_signals && modal.key_signals.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {modal.key_signals.map((s, i) => (
                            <span key={i} style={{ 
                              fontSize: "10px", 
                              padding: "2px 8px", 
                              background: "rgba(34, 197, 94, 0.1)", 
                              color: "var(--green)", 
                              borderRadius: "10px",
                              border: "1px solid rgba(34, 197, 94, 0.2)"
                            }}>
                              SIG: {s}
                            </span>
                          ))}
                        </div>
                      )}
                      {modal.red_flags && modal.red_flags.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                          {modal.red_flags.map((f, i) => (
                            <span key={i} style={{ 
                              fontSize: "10px", 
                              padding: "2px 8px", 
                              background: "rgba(239, 68, 68, 0.1)", 
                              color: "var(--red)", 
                              borderRadius: "10px",
                              border: "1px solid rgba(239, 68, 68, 0.2)"
                            }}>
                              FLAG: {f}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Match Insights (Explainability) */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 20 }}>
                <div style={{ background: "rgba(34, 197, 94, 0.05)", border: "1px solid rgba(34, 197, 94, 0.2)", borderRadius: "var(--radius-sm)", padding: 12 }}>
                  <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--green)", marginBottom: 8, letterSpacing: "0.05em" }}>MATCH STRENGTHS</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {modal.strengths && modal.strengths.length > 0 ? modal.strengths.map((s, i) => (
                      <div key={i} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "flex", gap: 6 }}>
                        <CheckCircle size={12} className="text-green" style={{ flexShrink: 0, marginTop: 2 }} /> {s}
                      </div>
                    )) : <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>No notable strengths.</div>}
                  </div>
                </div>
                <div style={{ background: "rgba(239, 68, 68, 0.05)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "var(--radius-sm)", padding: 12 }}>
                  <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--red)", marginBottom: 8, letterSpacing: "0.05em" }}>MATCH GAPS</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {modal.gaps && modal.gaps.length > 0 ? modal.gaps.map((g, i) => (
                      <div key={i} style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "flex", gap: 6 }}>
                        <X size={12} className="text-red" style={{ flexShrink: 0, marginTop: 2 }} /> {g}
                      </div>
                    )) : <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>No significant gaps.</div>}
                  </div>
                </div>
              </div>

              {/* Recruiter note */}
              <div style={{
                background: "var(--blue-light)",
                border: "1.5px solid var(--blue-mid)",
                borderLeftWidth: 3,
                borderLeftColor: "var(--blue)",
                padding: "12px 14px",
                marginBottom: 20,
              }}>
                <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--blue)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 4, letterSpacing: "0.08em" }}>
                  RECRUITER NOTE
                </div>
                <div style={{ fontSize: "0.875rem", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: 1.6 }}>
                  {modal.recruiter_note}
                </div>
              </div>

              {/* Transcript */}
              {(() => {
                const turns = transcripts[modal.candidate_id];
                if (!turns || turns.length === 0) return (
                  <div style={{ textAlign: "center", padding: "24px 0", color: "var(--text-muted)", fontSize: "0.875rem" }}>
                    No conversation transcript available.
                  </div>
                );
                return (
                  <div>
                    <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 12, letterSpacing: "0.08em", textTransform: "uppercase" }}>
                      Conversation Transcript · {turns.length} turns
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                      {turns.map((t, i) => {
                        const isAgent = !t.speaker?.toLowerCase().includes("candidate");
                        return (
                          <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: isAgent ? "flex-start" : "flex-end" }}>
                            <div style={{ fontSize: "10px", color: "var(--text-muted)", fontFamily: "'JetBrains Mono', monospace", marginBottom: 3, display: "flex", gap: 4, alignItems: "center" }}>
                              {isAgent ? <><Bot size={12}/> AI Recruiter</> : <><User size={12}/> {modal.candidate_name}</>}
                            </div>
                            <div className={isAgent ? "bubble-agent" : "bubble-candidate"}>
                              {t.message}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })()}

              {/* Recruiter Actions */}
              <div style={{ marginTop: 32, paddingTop: 20, borderTop: "1px solid var(--border)", display: "flex", gap: 10 }}>
                <button className="btn btn-primary" style={{ flex: 1, justifyContent: "center" }} onClick={() => alert("Scheduling interview for " + modal.candidate_name)}>
                  Schedule Interview
                </button>
                <button className="btn btn-outline" style={{ flex: 1, justifyContent: "center" }} onClick={() => alert("Candidate added to ATS shortlist")}>
                  Move to ATS
                </button>
                <button className="btn btn-outline" style={{ color: "var(--red)", borderColor: "var(--red-mid)" }} onClick={() => alert("Candidate rejected")}>
                  Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default function ShortlistPage() {
  return (
    <Suspense fallback={<div style={{ padding: 32, color: "var(--text-muted)" }}>Loading...</div>}>
      <ShortlistInner />
    </Suspense>
  );
}
