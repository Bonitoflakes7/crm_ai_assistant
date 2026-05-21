# HCP CRM – AI-First Log Interaction Screen

An AI-first CRM module for pharmaceutical field representatives to log Healthcare Professional (HCP) interactions using natural language — no manual form filling required.

---

## How It Works

Type a natural description in the AI chat panel (right side). The LangGraph agent parses it and automatically fills the form (left side).

**Example:**
> "Today I met with Dr. Smith and discussed product X efficiency. The sentiment was positive and I shared the brochures."

The AI instantly fills: HCP Name, Date, Topics Discussed, Sentiment, Materials Shared — zero manual input.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Redux Toolkit |
| Backend | Python + FastAPI |
| AI Agent | LangGraph |
| LLM | Groq (`llama-3.3-70b-versatile`) |
| Database | PostgreSQL (Railway) |
| Font | Google Inter |

---

## LangGraph Agent — 5 Tools

| # | Tool | Purpose |
|---|---|---|
| 1 | `log_interaction` | Extracts HCP name, date, sentiment, materials, topics from natural language |
| 2 | `edit_interaction` | Updates only the specific fields the user wants to correct |
| 3 | `suggest_followups` | Generates 3–4 actionable follow-up recommendations |
| 4 | `search_hcp` | Searches HCP records for autocomplete and verification |
| 5 | `summarize_topics` | Condenses verbose discussion notes into concise key points |

---

## Project Structure

```
hcp-crm/
├── frontend/                  # React + Redux
│   ├── src/
│   │   ├── store/
│   │   │   ├── store.js
│   │   │   ├── formSlice.js   # Form state (Redux)
│   │   │   └── chatSlice.js   # Chat state (Redux)
│   │   ├── components/
│   │   │   ├── InteractionForm.jsx
│   │   │   ├── AIAssistant.jsx
│   │   │   └── ChatMessage.jsx
│   │   ├── hooks/useAPI.js    # Axios API calls
│   │   ├── App.jsx
│   │   └── index.css
│   ├── .env.example
│   └── package.json
│
├── backend/                   # FastAPI + LangGraph
│   ├── app/
│   │   ├── main.py            # FastAPI app entry
│   │   ├── config.py          # Settings (pydantic-settings)
│   │   ├── agent/
│   │   │   ├── tools.py       # All 5 LangGraph tools
│   │   │   └── graph.py       # LangGraph StateGraph
│   │   ├── models/
│   │   │   ├── interaction.py # SQLAlchemy models
│   │   │   └── schemas.py     # Pydantic schemas
│   │   ├── db/database.py     # PostgreSQL session
│   │   └── routes/
│   │       └── interactions.py
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL database
- Groq API key

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in your GROQ_API_KEY and DATABASE_URL in .env
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
# Set VITE_API_URL=http://localhost:8000/api
npm run dev
```

Open http://localhost:5173

### Seed Demo HCPs (optional)

```bash
curl -X POST http://localhost:8000/api/hcps/seed
```

---

## Deployment

### Backend → Railway
1. Create Railway project → add PostgreSQL
2. Deploy backend service → set env vars:
   - `GROQ_API_KEY`
   - `DATABASE_URL` (from Railway PostgreSQL)
   - `FRONTEND_URL` (your Vercel URL)

### Frontend → Vercel
1. Push frontend folder to GitHub
2. Import to Vercel
3. Set env var: `VITE_API_URL=https://your-backend.railway.app/api`

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | Send message to AI agent, get form updates |
| POST | `/api/interactions` | Save finalized interaction to DB |
| GET | `/api/interactions` | List recent interactions |
| GET | `/api/hcps/search?q=` | Search HCP records |
| POST | `/api/hcps/seed` | Seed demo HCP data |
| GET | `/api/health` | Health check |

---

## Example Interactions

**Log a new interaction:**
> "Met Dr. Priya Patel today at 3pm, discussed oncology drug X efficacy. She was very interested — positive sentiment. Shared clinical trial PDF and distributed 2 samples."

**Edit a field:**
> "Actually sorry, the sentiment was neutral, not positive."

**Summarize:**
> "Summarize the topics discussed."

**Follow-ups:**
> Follow-up suggestions appear automatically after every log.
