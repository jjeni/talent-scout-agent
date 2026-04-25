"use client";
import { FileSpreadsheet, Download, HelpCircle } from "lucide-react";

const SAMPLE_CSV_DATA = [
  { id: "cand_001", name: "Alice Johnson", skills: '"React, Node.js, PostgreSQL"', exp: "6", loc: "Remote", email: "alice@email.com", edu: "Bachelor's CS" },
  { id: "cand_002", name: "Bob Chen", skills: '"Python, FastAPI, Docker"', exp: "8", loc: "San Francisco CA", email: "bob@email.com", edu: "Master's SE" },
  { id: "cand_003", name: "Priya Nair", skills: '"React, TypeScript, GraphQL"', exp: "5", loc: "Remote", email: "priya@email.com", edu: "Bachelor's CS" },
];

export default function TemplatePage() {
  return (
    <>
      <div className="topbar">
        <FileSpreadsheet size={18} className="text-blue" />
        <span className="topbar-title">CSV Template</span>
        <span className="topbar-sub">Batch Candidate Source</span>
      </div>

      <div className="page fade-in-up" style={{ maxWidth: 1000, margin: "0 auto", paddingBottom: 64 }}>
        <div style={{ marginBottom: 40, display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 20 }}>
          <div>
            <h1 style={{ fontSize: "clamp(1.6rem, 4vw, 2.2rem)", fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.15, marginBottom: 12 }}>
              Batch Candidate Data <br />
              <span style={{ color: "var(--blue)" }}>CSV Formatting Requirements</span>
            </h1>
            <p style={{ color: "var(--text-muted)", fontSize: "0.95rem", maxWidth: 540 }}>
              To pipeline a large set of structural candidate profiles into TalentScout, ensure your CSV columns exactly match the fields below.
            </p>
          </div>
          
          <div style={{ marginTop: 8 }}>
            <a href="/data/candidates_template.csv" download className="btn btn-primary" style={{ textDecoration: "none" }}>
              <Download size={16} /> Download .CSV
            </a>
          </div>
        </div>

        <div className="card" style={{ padding: 0, overflow: "hidden", marginBottom: 32 }}>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>id</th>
                  <th>name</th>
                  <th>skills</th>
                  <th>experience_years</th>
                  <th>location</th>
                  <th>email</th>
                  <th>education</th>
                </tr>
              </thead>
              <tbody>
                {SAMPLE_CSV_DATA.map((row) => (
                  <tr key={row.id}>
                    <td style={{ fontFamily: "'JetBrains Mono', monospace", color: "var(--text-muted)", fontSize: "12px" }}>{row.id}</td>
                    <td><strong style={{ color: "var(--text-primary)" }}>{row.name}</strong></td>
                    <td style={{ color: "var(--green)" }}>{row.skills}</td>
                    <td style={{ textAlign: "center", color: "var(--amber)", fontWeight: 600 }}>{row.exp}</td>
                    <td>{row.loc}</td>
                    <td style={{ color: "var(--blue)" }}>{row.email}</td>
                    <td>{row.edu}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card" style={{ padding: "28px" }}>
          <div className="card-title" style={{ color: "var(--blue)", marginBottom: 16 }}>
            <HelpCircle size={14} /> Field Guidelines
          </div>
          <ul style={{ display: "flex", flexDirection: "column", gap: 12, margin: 0, paddingLeft: 20, color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.6 }}>
            <li><strong>id:</strong> A unique string identifier for each candidate.</li>
            <li><strong>skills:</strong> Comma-separated list. Wrap the field in quotes (e.g. <code>"React, AWS, Node"</code>).</li>
            <li><strong>experience_years:</strong> Numeric integer value representing career duration.</li>
            <li><strong>Optional fields:</strong> <code>email</code> and <code>education</code> can be left empty, but the headers must exist.</li>
          </ul>
        </div>
      </div>
    </>
  );
}
