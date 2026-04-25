"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { Rocket, RadioReceiver, Trophy, FileSpreadsheet, BookOpen, Menu, X, Info } from "lucide-react";

const NAV = [
  { href: "/",          icon: Rocket, label: "Launchpad" },
  { href: "/pipeline",  icon: RadioReceiver, label: "Pipeline"  },
  { href: "/shortlist", icon: Trophy, label: "Shortlist"  },
  { href: "/guide",     icon: Info, label: "User Guide" },
];

export default function Sidebar() {
  const path = usePathname();
  const [open, setOpen] = useState(false);

  // Close on route change
  useEffect(() => { setOpen(false); }, [path]);

  // Lock body scroll when open
  useEffect(() => {
    if (open) document.body.style.overflow = "hidden";
    else document.body.style.overflow = "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  return (
    <>
      {/* Mobile top bar */}
      <div className="mobile-topbar">
        <button className="hamburger" onClick={() => setOpen(v => !v)} aria-label="Toggle menu">
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
        <span style={{ fontWeight: 800, fontSize: "0.95rem", letterSpacing: "-0.02em" }}>
          TalentScout AI
        </span>
        <span style={{ marginLeft: "auto", fontFamily: "'JetBrains Mono', monospace", fontSize: "10px", color: "var(--text-muted)" }}>
          Gemini 2.5
        </span>
      </div>

      {/* Overlay */}
      {open && (
        <div
          className="sidebar-overlay"
          style={{ display: "block" }}
          onClick={() => setOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${open ? "open" : ""}`}>
        {/* Mac OS Dots */}
        <div className="mac-dots">
          <span className="mac-dot" style={{ background: "#ff5f56" }} />
          <span className="mac-dot" style={{ background: "#ffbd2e" }} />
          <span className="mac-dot" style={{ background: "#27c93f" }} />
        </div>

        {/* Logo */}
        <div className="sidebar-logo">
          <div className="sidebar-logo-icon-box">
            <Rocket size={20} color="#fff" />
          </div>
          <div className="sidebar-logo-text">
            <h1 className="sidebar-app-name">TalentScout<sup style={{fontSize: "10px", fontWeight: "normal"}}>™</sup></h1>
            <span className="sidebar-logo-sub">AI Recruitment</span>
          </div>
        </div>


        {/* Navigation */}
        <nav className="sidebar-nav">
          <div className="nav-section-label">General</div>
          {NAV.map(({ href, icon: Icon, label }) => (
            <Link
              key={href}
              href={href}
              className={`nav-item ${path === href ? "active" : ""}`}
            >
              <span className="nav-icon"><Icon size={18} /></span>
              {label}
            </Link>
          ))}

          <div className="nav-section-label" style={{ marginTop: 16 }}>Resources</div>
          <Link
            href="/template"
            className={`nav-item ${path === "/template" ? "active" : ""}`}
          >
            <span className="nav-icon"><FileSpreadsheet size={18} /></span>
            CSV Template
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="nav-item"
          >
            <span className="nav-icon"><BookOpen size={18} /></span>
            API Docs
          </a>
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="sidebar-status">
            <span className="status-dot" />
            Gemini 2.5 Flash · Online
          </div>
          <div style={{ marginTop: 12, fontSize: "10px", color: "var(--amber)", fontWeight: 500, display: "flex", alignItems: "center", gap: 4 }}>
            <span style={{ width: 4, height: 4, borderRadius: "50%", background: "var(--amber)" }} />
            Privacy First: Keys are never stored
          </div>
          <div style={{ marginTop: 6, fontFamily: "'JetBrains Mono', monospace", fontSize: "10px", color: "var(--text-muted)" }}>
            Catalyst Hackathon 2026
          </div>
        </div>
      </aside>
    </>
  );
}
