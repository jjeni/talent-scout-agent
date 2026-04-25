# 🤖 TalentScout AI — AI-Powered Talent Scouting & Engagement Agent

> **Catalyst Hackathon 2026** · [Demo Video](#) · [Deployed App](#)

An end-to-end AI pipeline that **parses job descriptions, scores candidates, conducts simulated multi-turn outreach, and delivers explainable ranked shortlists** — powered by Google Gemini 2.0 Flash.

---

## 🚀 Quick Start (< 5 minutes)

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google Gemini API key → [Get one free](https://aistudio.google.com/)

### 1. Clone & Configure
```bash
git clone https://github.com/your-username/talent-scout.git
cd "talent-scout"

# Copy and fill in your API key
cp backend/.env.example backend/.env
# Edit backend/.env — set GEMINI_API_KEY=your_key_here
```

### 2. Install Backend
```bash
pip3 install --user -r backend/requirements.txt
```

### 3. Install Frontend
```bash
cd frontend && npm install && cd ..
```

### 4. Run Everything
```bash
bash start.sh
```

Open **http://localhost:3000** — paste a JD and click Launch Pipeline 🎉

---

## 🏗️ Architecture

```
JD Text Input
     │
     ▼
┌─────────────────┐
│  Stage 1        │  Gemini 2.0 Flash → structured JSON
│  JD Parser      │  (role, skills+weights, experience, location, salary)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 2a       │  Auto-detects: CSV · JSON · PDF · DOCX · GitHub · LinkedIn
│  Candidate      │  → Unified Profile Schema (50+ synthetic candidates built-in)
│  Ingestor       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 2b       │  Hard filters → Hybrid match scoring
│  Matcher        │  Skills: text-embedding-004 cosine + exact match (40%)
│                 │  Experience (25%) + Location (20%) + Education (15%)
└────────┬────────┘
         │ Top-N candidates
         ▼
┌─────────────────┐
│  Stage 3        │  Gemini dual-model: Agent persona + Candidate persona
│  Conversation   │  3–5 turns per candidate, personalised per profile
│  Agent          │  → Full transcript stored
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 4        │  Combined Score = 60% Match + 40% Interest
│  Ranker         │  AI-generated recruiter note per candidate
└────────┬────────┘
         │
         ▼
  Ranked Shortlist (JSON + UI Dashboard)
```

---

## 📊 Scoring Model

### Match Score (0–100)
| Dimension | Weight | Method |
|---|---|---|
| Skills Match | 40% | `text-embedding-004` cosine + exact normalization |
| Experience Fit | 25% | Years vs JD requirement (with overqualified penalty) |
| Location Fit | 20% | Remote/timezone/city compatibility logic |
| Education Fit | 15% | Degree rank hierarchy + field relevance |

### Interest Score (0–100)
| Dimension | Weight | Source |
|---|---|---|
| Stated Interest | 35% | Explicit positive/negative statements |
| Engagement Depth | 25% | Question depth, reply richness |
| Availability | 20% | Notice period, start date |
| Sentiment | 20% | Overall emotional tone |

### Combined Score
```
Combined = 0.60 × Match + 0.40 × Interest
```
*(Weights configurable from the UI)*

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLM (Primary)** | Google Gemini 2.0 Flash |
| **Embeddings** | Google `text-embedding-004` |
| **LLM (Fallback)** | OpenAI GPT-4o |
| **Backend** | FastAPI + Python 3.10 |
| **Frontend** | Next.js 14 (App Router) |
| **Candidate Input** | CSV · JSON · PDF · DOCX · GitHub API · LinkedIn scraping |
| **Real-time** | Server-Sent Events (SSE) |
| **Deployment** | Vercel (frontend) + Render (backend) |

---

## 🎯 Sample Input / Output

**Input JD:** Senior Full-Stack Engineer — FinTech Startup (Series B), Remote US, $160k–$200k, React + Node.js + AWS

**Sample Output:**
| Rank | Candidate | Match | Interest | Combined | Top Reason |
|---|---|---|---|---|---|
| #1 | Priya Nair | 91 | 87 | 89.8 | 6y React/Node, AWS certified, remote-ready |
| #2 | James Okafor | 85 | 92 | 87.8 | FinTech background, Stripe exp, high enthusiasm |
| #3 | Sofia Hernandez | 88 | 74 | 82.4 | Strong full-stack, PostgreSQL expert |

---

## 📁 Project Structure

```
talent-scout/
├── backend/
│   ├── main.py                    # FastAPI app + all routes
│   ├── models/                    # Pydantic schemas (JD, Candidate, Output)
│   ├── modules/
│   │   ├── jd_parser.py           # Stage 1
│   │   ├── candidate_ingestor.py  # Stage 2a (multi-format)
│   │   ├── matcher.py             # Stage 2b (hybrid scoring)
│   │   ├── conversation_agent.py  # Stage 3 (dual-model LLM)
│   │   ├── interest_scorer.py     # Stage 3b (transcript analysis)
│   │   └── ranker.py              # Stage 4
│   └── data/candidates.py         # 50 synthetic candidates
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # JD input + settings
│   │   ├── pipeline/page.tsx      # Live progress (SSE)
│   │   └── shortlist/page.tsx     # Ranked shortlist dashboard
│   └── lib/api.ts                 # TypeScript API client
└── start.sh                       # One-command startup
```

---

## ✅ Submission Checklist

- [x] Deployed prototype (see link above)
- [x] Public source code repo with comprehensive README
- [x] Architecture diagram (see above)
- [x] 2+ sample JD inputs with outputs (see `/backend/data/`)
- [x] Match Score with per-dimension sub-scores
- [x] Interest Score with per-dimension sub-scores from conversation
- [x] Final ranked shortlist combining both scores
- [x] Structured Match Insights (Strengths/Gaps explainability)
- [x] Recruiter Action Dashboard (Schedule/Reject directly from UI)
- [x] Enhanced Screening (Career goals & Notice period captures)
- [x] Multi-source Discovery (CSV, LinkedIn, GitHub, Resumes)
- [x] Fully Mobile Responsive recruitment dashboard

---

*Built for Catalyst Hackathon 2026 · Powered by Google Gemini 2.0 Flash*
