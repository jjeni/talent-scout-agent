# 🤖 TalentScout AI — AI-Powered Talent Scouting & Engagement Agent

> **Catalyst Hackathon 2026** · [Demo Video](https://drive.google.com/file/d/19GmMk1dXNOn1_zX5B_Wwp-Fk63PgSysQ/view?usp=drivesdk) · [Deployed App](https://hr-scout-agent.vercel.app/)

An end-to-end AI pipeline that **parses job descriptions, discovers matching candidates, engages them conversationally to assess genuine interest, and outputs a ranked shortlist** scored on two dimensions: **Match Score** and **Interest Score** — powered by Google Gemini, OpenAI GPT, Anthropic Claude, and xAI Grok.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **Multi-Provider LLM** | Plug in your own API key for **Gemini 2.5 Flash**, **GPT-5.4 Mini**, **Claude 4.6 Opus**, **Grok-1**, or **OpenRouter** (100+ models) |
| **Live Chat Simulation** | Watch the AI Recruiter and Candidate interact turn-by-turn in a real-time chat UI streamed via SSE |
| **Instant JD Verification** | See the structured data (role, skills, seniority, location) the AI extracted — before matching begins |
| **Explainable Scoring** | Every candidate gets a transparent breakdown: Strengths, Gaps, Key Signals, and Red Flags |
| **Real-time Activity Feed** | Terminal-style log tracks every pipeline event with timestamps and progress |
| **Multi-Source Discovery** | Ingest candidates from CSV, JSON, PDF/DOCX Resumes, GitHub profiles, and LinkedIn URLs |
| **Recruiter Actions** | Schedule interviews, move to ATS, or reject — directly from the shortlist dashboard |

---

## 🚀 Local Setup Guide

### Prerequisites

| Tool | Version | Get it |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | [nodejs.org](https://nodejs.org/) |
| Git | any | [git-scm.com](https://git-scm.com/) |
| API Key | at least one | [Google AI Studio](https://aistudio.google.com/) · [OpenAI](https://platform.openai.com/) · [Anthropic](https://console.anthropic.com/) |

---

### 🪟 Windows Setup

#### 1. Clone the Repository
```powershell
git clone https://github.com/jjeni/talent-scout-agent.git
cd talent-scout-agent
```

#### 2. Configure Environment Variables
```powershell
copy backend\.env.example backend\.env
# Open backend\.env in notepad and add your API key(s)
notepad backend\.env
```

#### 3. Install Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

#### 4. Install Frontend
```powershell
cd frontend
npm install
cd ..
```

#### 5. Run (two separate terminals)
**Terminal 1 — Backend:**
```powershell
cd backend
.\venv\Scripts\activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm run dev
```

Open **http://localhost:3000** 🎉

---

### 🍎 macOS / 🐧 Linux Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/jjeni/talent-scout-agent.git
cd talent-scout-agent
```

#### 2. Configure Environment Variables
```bash
cp backend/.env.example backend/.env
# Open and add your API key(s)
nano backend/.env
```

#### 3. Install Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

#### 4. Install Frontend
```bash
cd frontend
npm install
cd ..
```

#### 5. Run (two separate terminals)
**Terminal 1 — Backend:**
```bash
cd backend
source venv/bin/activate
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

Open **http://localhost:3000** 🎉

---

### ⚡ Quick Start (One Command)
If you prefer a single script:
```bash
chmod +x start.sh
./start.sh
```

---

## 🔑 Environment Variables

Create `backend/.env` from the example file. Only **one** API key is required.

```env
# --- REQUIRED (at least one) ---
GEMINI_API_KEY=your_gemini_api_key_here

# --- OPTIONAL (use any provider you prefer) ---
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
XAI_API_KEY=your_xai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

> 💡 **Tip:** You can also enter API keys directly in the web UI under **LLM Configuration → Own Key**. Keys are stored in your browser's local storage and never sent to any server other than the LLM provider.

---

## 🏗️ Architecture — Detailed

### High-Level Pipeline Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                        RECRUITER (Browser)                          │
│  ┌──────────┐  ┌──────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │Launchpad │─▶│Pipeline View │─▶│  Shortlist   │  │   Guide     │  │
│  │(JD Input)│  │(Real-time)   │  │  Dashboard   │  │   Page      │  │
│  └──────────┘  └──────┬───────┘  └─────────────┘  └─────────────┘  │
│                       │ SSE Stream                                   │
└───────────────────────┼──────────────────────────────────────────────┘
                        │ HTTP + Server-Sent Events
┌───────────────────────┼──────────────────────────────────────────────┐
│                  FASTAPI BACKEND (Port 8000)                         │
│                       │                                              │
│  ┌────────────────────▼────────────────────────────────────────┐     │
│  │              Pipeline Orchestrator (main.py)                │     │
│  │  Manages stage transitions, SSE emission, error handling    │     │
│  └──┬──────────┬──────────┬───────────────┬───────────┬───────┘     │
│     │          │          │               │           │              │
│     ▼          ▼          ▼               ▼           ▼              │
│  ┌──────┐ ┌────────┐ ┌────────┐   ┌───────────┐ ┌────────┐         │
│  │Parse │ │Ingest  │ │Match   │   │Converse   │ │Rank    │         │
│  │JD    │ │Cands   │ │& Score │   │(Simulate) │ │& Sort  │         │
│  └──┬───┘ └───┬────┘ └───┬────┘   └─────┬─────┘ └───┬────┘         │
│     │         │          │               │           │              │
│     ▼         ▼          ▼               ▼           ▼              │
│  ┌─────────────────────────────────────────────────────────┐        │
│  │            Unified LLM Gateway (llm_utils.py)           │        │
│  │  Routes to: Gemini │ OpenAI │ Anthropic │ xAI │ OpenR. │        │
│  └─────────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────────┘
```

### Stage-by-Stage Breakdown

```
 ╔═══════════════════════════════════════════════════════════════════════╗
 ║  STAGE 1 — JD PARSING                                               ║
 ║                                                                      ║
 ║  Input:  Raw JD text (pasted by recruiter)                           ║
 ║  Model:  Gemini 2.5 Flash / GPT-5.4 Mini / Claude 4.6 Opus          ║
 ║  Output: JDSchema {                                                  ║
 ║            role_title, seniority, employment_type,                    ║
 ║            location {type, city, country},                            ║
 ║            experience {min_years, preferred_years},                   ║
 ║            required_skills [{skill, importance}],                     ║
 ║            nice_to_have_skills, education, compensation               ║
 ║          }                                                            ║
 ║  UI:     → Parsed JD card appears in pipeline view                   ║
 ╠═══════════════════════════════════════════════════════════════════════╣
 ║  STAGE 2a — CANDIDATE INGESTION                                      ║
 ║                                                                      ║
 ║  Sources:  Built-in dataset (50 synthetic profiles)                   ║
 ║            + CSV/JSON batch files                                     ║
 ║            + PDF/DOCX resumes (LLM-parsed)                            ║
 ║            + GitHub profile URLs                                      ║
 ║            + LinkedIn profile URLs                                    ║
 ║  Output:   List[UnifiedCandidateProfile]                              ║
 ╠═══════════════════════════════════════════════════════════════════════╣
 ║  STAGE 2b — MATCHING & SCORING                                       ║
 ║                                                                      ║
 ║  Method:   Hybrid (Embeddings + Rules)                                ║
 ║                                                                       ║
 ║  ┌─────────────────┬─────────┬───────────────────────────────────┐    ║
 ║  │ Dimension       │ Weight  │ Method                            │    ║
 ║  ├─────────────────┼─────────┼───────────────────────────────────┤    ║
 ║  │ Skills Match    │   40%   │ gemini-embedding-001 cosine sim + │    ║
 ║  │                 │         │ exact keyword normalization       │    ║
 ║  │ Experience Fit  │   25%   │ Years vs JD min/preferred         │    ║
 ║  │                 │         │ (overqualified penalty applied)   │    ║
 ║  │ Location Fit    │   20%   │ Remote/timezone/city compat.      │    ║
 ║  │ Education Fit   │   15%   │ Degree rank hierarchy + field     │    ║
 ║  └─────────────────┴─────────┴───────────────────────────────────┘    ║
 ║                                                                       ║
 ║  Hard Filters:  Candidates below threshold → excluded with reasons    ║
 ║  Output:        Top-N ScoredCandidates (sorted by match_score)        ║
 ╠═══════════════════════════════════════════════════════════════════════╣
 ║  STAGE 3 — CONVERSATIONAL OUTREACH (SIMULATED)                       ║
 ║                                                                       ║
 ║  For each Top-N candidate:                                            ║
 ║    1. Generate AI Recruiter persona (warm, professional)              ║
 ║    2. Generate Candidate persona (based on actual profile data)       ║
 ║    3. Run 3-turn conversation simulation                              ║
 ║    4. Stream each turn to UI via SSE (real-time chat bubbles)         ║
 ║    5. Analyze transcript → InterestBreakdown                          ║
 ║                                                                       ║
 ║  Interest Score Dimensions:                                           ║
 ║  ┌───────────────────┬─────────┬─────────────────────────────────┐    ║
 ║  │ Dimension         │ Weight  │ Source                          │    ║
 ║  ├───────────────────┼─────────┼─────────────────────────────────┤    ║
 ║  │ Stated Interest   │   35%   │ Explicit yes/no/maybe signals   │    ║
 ║  │ Engagement Depth  │   25%   │ Question depth, reply richness  │    ║
 ║  │ Availability      │   20%   │ Notice period, start date       │    ║
 ║  │ Sentiment         │   20%   │ Overall emotional tone          │    ║
 ║  └───────────────────┴─────────┴─────────────────────────────────┘    ║
 ║                                                                       ║
 ║  Output: ConversationTranscript + InterestBreakdown per candidate     ║
 ╠═══════════════════════════════════════════════════════════════════════╣
 ║  STAGE 4 — RANKING & SHORTLISTING                                    ║
 ║                                                                       ║
 ║  Combined Score = (wMatch × Match) + (wInterest × Interest)           ║
 ║  Default weights: 60% Match / 40% Interest (configurable in UI)       ║
 ║                                                                       ║
 ║  For each ranked candidate, the LLM generates:                        ║
 ║    • recruiter_note  — one-line actionable recommendation             ║
 ║    • strengths       — what makes them a great fit                    ║
 ║    • gaps            — what's missing or concerning                   ║
 ║    • key_signals     — notable quotes from conversation               ║
 ║    • red_flags       — concerning behavioral signals                  ║
 ║                                                                       ║
 ║  Output: ShortlistOutput (JSON) → Rendered in Shortlist Dashboard     ║
 ╚═══════════════════════════════════════════════════════════════════════╝
```

### Real-Time Communication

```
  Browser (Next.js)                     FastAPI Backend
  ═══════════════                       ══════════════
        │                                     │
        │── POST /api/pipeline/start ────────▶│  Starts background task
        │                                     │
        │── GET  /api/pipeline/status/{id} ──▶│  Opens SSE stream
        │                                     │
        │◀── SSE: {stage: "parsing_jd"} ──────│  Stage 1 updates
        │◀── SSE: {parsed_jd: {...}} ─────────│  Parsed JD data
        │◀── SSE: {stage: "ingesting"} ───────│  Stage 2a
        │◀── SSE: {stage: "matching"} ────────│  Stage 2b + per-candidate
        │◀── SSE: {stage: "conversing",  ─────│  Stage 3
        │         last_turn: {agent, cand}}   │  Live chat turns
        │◀── SSE: {stage: "ranking"} ─────────│  Stage 4
        │◀── SSE: {stage: "done"} ────────────│  Complete
        │                                     │
        │── GET  /api/shortlist/{id} ────────▶│  Fetch final results
        │◀── JSON: ShortlistOutput ───────────│
        │                                     │
```

---

## 📁 Project Structure

```
talent-scout-agent/
├── backend/
│   ├── main.py                        # FastAPI app, routes, SSE, pipeline orchestrator
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Environment variable template
│   ├── models/
│   │   ├── jd_schema.py               # JDSchema, SkillEntry, LocationSchema, etc.
│   │   ├── candidate_schema.py        # UnifiedCandidateProfile
│   │   └── output_schema.py           # MatchBreakdown, InterestBreakdown, PipelineStatus
│   ├── modules/
│   │   ├── jd_parser.py               # Stage 1 — LLM-powered JD parsing
│   │   ├── candidate_ingestor.py      # Stage 2a — Multi-source ingestion
│   │   ├── matcher.py                 # Stage 2b — Hybrid match scoring
│   │   ├── conversation_agent.py      # Stage 3 — Dual-persona chat simulation
│   │   ├── interest_scorer.py         # Stage 3b — Transcript → Interest score
│   │   ├── ranker.py                  # Stage 4 — Combined ranking + recruiter notes
│   │   └── scrapers/                  # GitHub & LinkedIn profile scrapers
│   ├── utils/
│   │   └── llm_utils.py              # Unified LLM gateway (Gemini/OpenAI/Claude/xAI/OR)
│   └── data/
│       └── candidates.py              # 50 synthetic candidate profiles for testing
├── frontend/
│   ├── app/
│   │   ├── page.tsx                   # Launchpad — JD input, source config, LLM selector
│   │   ├── pipeline/page.tsx          # Pipeline — Real-time simulation dashboard
│   │   ├── shortlist/page.tsx         # Shortlist — Ranked results with modals
│   │   ├── guide/page.tsx             # Guide — How to use the dashboard
│   │   ├── layout.tsx                 # Root layout with fonts and global styles
│   │   └── globals.css                # Design system (CSS variables, components)
│   └── lib/
│       └── api.ts                     # TypeScript API client + SSE subscriber
├── samples/
│   ├── sample_jd.txt                  # Example job description input
│   └── sample_output.json             # Example ranked shortlist output
└── start.sh                           # One-command startup script
```

---

## 🎯 Sample Input / Output

**Input JD:** Senior Full-Stack Engineer — FinTech Startup, Remote US, $160k–$200k, React + Node.js + AWS

**Sample Output:**

| Rank | Candidate | Match | Interest | Combined | Top Reason |
|---|---|---|---|---|---|
| 🥇 #1 | Priya Nair | 91 | 87 | 89.6 | 6y React/Node, AWS certified, remote-ready |
| 🥈 #2 | James Okafor | 85 | 92 | 88.1 | FinTech background, Stripe exp, high enthusiasm |
| 🥉 #3 | Sofia Hernandez | 88 | 74 | 82.4 | Strong full-stack, PostgreSQL expert |

See [`samples/`](./samples/) for complete input/output examples.

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLMs** | Gemini 2.5 Flash · GPT-5.4 Mini · Claude 4.6 Opus · Grok-1 · OpenRouter |
| **Embeddings** | Google `gemini-embedding-001` |
| **Backend** | FastAPI · Python 3.10 · Pydantic v2 |
| **Frontend** | Next.js 14 (App Router) · React 18 |
| **Styling** | Vanilla CSS · Glassmorphism · Micro-animations |
| **Icons** | Lucide React |
| **Real-time** | Server-Sent Events (SSE) |

---

## ✅ Assignment Checklist

- [x] **Working prototype** — fully functional local setup with clear instructions
- [x] **Source code in public repo** — [github.com/jjeni/talent-scout-agent](https://github.com/jjeni/talent-scout-agent)
- [x] **Architecture diagram** — detailed stage-by-stage breakdown (see above)
- [x] **JD Parsing** — LLM extracts structured role requirements
- [x] **Candidate Discovery & Matching** — multi-source + hybrid scoring with explainability
- [x] **Conversational Outreach (Simulated)** — real-time dual-persona chat with SSE streaming
- [x] **Match Score** — 4-dimension weighted breakdown (Skills 40%, Experience 25%, Location 20%, Education 15%)
- [x] **Interest Score** — 4-dimension breakdown from transcript analysis (Stated 35%, Engagement 25%, Availability 20%, Sentiment 20%)
- [x] **Combined Ranked Output** — configurable weights, AI recruiter notes, actionable shortlist
- [x] **Sample inputs and outputs** — provided in `samples/` directory

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Built for Catalyst Hackathon 2026 · Powered by Gemini · GPT · Claude · Grok*
