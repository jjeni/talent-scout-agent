# 🤖 TalentScout AI — AI-Powered Talent Scouting & Engagement Agent

> **Catalyst Hackathon 2026** · [Demo Video](#) · [Deployed App](#)

An end-to-end AI pipeline that **parses job descriptions, scores candidates, conducts simulated multi-turn outreach, and delivers explainable ranked shortlists** — powered by Google Gemini, OpenAI, and Anthropic.

---

## ✨ Key Features

*   **Multi-Provider LLM Support**: Use **Gemini 2.5 Flash**, **GPT-5.4 Mini**, or **Claude 4.6 Opus** with your own API keys.
*   **Live Chat Simulation**: Watch the AI Recruiter and Candidates interact in real-time with a beautiful chat UI.
*   **Real-time Activity Feed**: A terminal-style log tracks every stage of the pipeline with millisecond precision.
*   **Instant JD Verification**: View the structured data (skills, seniority, location) extracted by the AI immediately after parsing.
*   **Multi-Source Discovery**: Ingest candidates from CSV, JSON, PDF Resumes, GitHub, and LinkedIn URLs.

---

## 🚀 Local Setup Guide

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** (with npm)
- An API Key from one of: [Google AI Studio](https://aistudio.google.com/), [OpenAI](https://platform.openai.com/), or [Anthropic](https://console.anthropic.com/).

### 1. Clone the Repository
```bash
git clone https://github.com/jjeni/talent-scout-agent.git
cd talent-scout-agent
```

### 2. Configure Environment Variables
Copy the example environment file and fill in your keys:
```bash
cp backend/.env.example backend/.env
```
*Note: You can also enter these keys directly in the web UI for testing.*

### 3. Install Backend Dependencies
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
cd ..
```

### 4. Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 5. Run the Application
You can run both servers using the provided script:
```bash
# Windows (PowerShell)
.\start.sh
```
Or manually:
*   **Backend**: `cd backend && python -m uvicorn main:app --reload` (Runs on port 8000)
*   **Frontend**: `cd frontend && npm run dev` (Runs on port 3000)

Open **http://localhost:3000** to begin scouting! 🎉

---

## 🏗️ Architecture

```
JD Text Input
     │
     ▼
┌─────────────────┐
│  Stage 1        │  JD Parser (Gemini/GPT/Claude)
│  JD Parser      │  ──▶ [Instant Verification UI]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 2        │  Ingestion & Matching
│  Ingestion &    │  Embeddings + Rules-based Hybrid Scoring
│  Matching       │  ──▶ [Live Activity Feed]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 3        │  Dual-Persona Conversation Simulation
│  Live Chat      │  ──▶ [Real-time Chat UI via SSE]
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Stage 4        │  Final Ranking & Shortlisting
│  Ranker         │  Combined Match + Interest Scores
└────────┬────────┘
         │
         ▼
   Ranked Shortlist (JSON + UI Dashboard)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **LLMs** | Gemini 2.5 Flash, GPT-5.4 Mini, Claude 4.6 Opus |
| **Embeddings** | Google `gemini-embedding-001` |
| **Backend** | FastAPI (Python) |
| **Frontend** | Next.js 14 (App Router) |
| **Styling** | Vanilla CSS (Modern Premium Aesthetic) |
| **Icons** | Lucide React |

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

*Built for Catalyst Hackathon 2026*
