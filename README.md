# HCP CRM — AI-First Log Interaction Screen

> Built as part of a technical assessment for a Life Science CRM product role.  
> The goal: design an AI-first CRM module where pharmaceutical field representatives log HCP interactions through natural language — no manual form filling.

---

## What This Is

A split-screen web application. On the left, a structured form for logging Healthcare Professional (HCP) interactions. On the right, an AI chat assistant powered by LangGraph and Groq.

**The core rule: you never touch the form. You talk to the AI.**

Type something like:

> *"Today I called Dr. Priya Patel at 2pm and discussed Drug X dosage protocols. She was very receptive. Shared the clinical trial brochure and distributed 2 samples."*

The AI extracts every detail and fills the form automatically — HCP name, interaction type, date, time, topics, materials, sentiment, outcomes.

---

## Live Demo

| Service | URL |
|---|---|
| Frontend | Deployed on Vercel |
| Backend API | Deployed on Railway |
| API Docs | `https://your-backend.railway.app/docs` |

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React 18 + Redux Toolkit | Component state + predictable global form state |
| Backend | Python 3.11 + FastAPI | Async, fast, auto-generates OpenAPI docs |
| AI Agent Framework | LangGraph | Stateful graph-based tool orchestration |
| LLM | Groq — `llama-3.1-8b-instant` | Low latency inference, tool calling support |
| Database | PostgreSQL (Railway) | Structured interaction records, JSON columns for arrays |
| ORM | SQLAlchemy 2.0 | Type-safe DB access with Pydantic integration |
| Font | Google Inter | As specified in the brief |

---

## How the AI Agent Works

The LangGraph agent uses a `StateGraph` with two nodes:

```
User Message
     │
     ▼
[agent node]  ← LLM decides which tool to call
     │
     ├── tool_calls present? → [tools node] → END
     │
     └── no tool calls? → END
```

**Key design decision:** The graph edge goes `tools → END`, not `tools → agent`. This means one LLM call per request — no looping, no timeouts. `suggest_followups` runs inline in Python after `log_interaction`, not through the graph.

Conversational messages (`"hi"`, `"thanks"`, `"okay"`) are intercepted before the LLM with a keyword check — zero API cost, instant response.

---

## The 5 LangGraph Tools

### Tool 1 — `log_interaction`
Extracts all form fields from a natural language interaction description.

**Handles:** HCP name, interaction type (Meeting/Call/Email/Conference), date, time, attendees, topics discussed, materials shared, samples distributed, sentiment, outcomes, follow-up actions.

**Try it:**
```
Today I called Dr. Sarah Smith at 3pm and discussed Product X efficacy 
and dosage for elderly patients. She was very interested — positive sentiment. 
Shared the Phase III clinical trial PDF and distributed 3 samples of Drug X.
```

---

### Tool 2 — `edit_interaction`
Updates **only** the fields explicitly mentioned. Nothing else changes.

**Key behavior:** If you say *"change the time to 14:30"* — only time updates. Sentiment, materials, HCP name, everything else stays exactly as it was. The LLM prompt explicitly forbids inferring unmentioned fields.

**Try it:**
```
Sorry, it was actually a Call not a Meeting
```
```
Change the time to 14:30
```
```
Actually the sentiment was neutral
```

---

### Tool 3 — `suggest_followups`
Generates 3–4 contextual, actionable follow-up recommendations based on the interaction. Runs automatically after every log. Suggestions are clickable — they append to the Follow-up Actions field.

**Try it:**
```
Suggest follow-up actions for this interaction
```

---

### Tool 4 — `search_hcp`
Fuzzy-searches the HCP database by name. Sets the HCP Name field with the best match.

**Try it:**
```
Search for Dr. Anjali
```
```
Find HCP named Sharma
```

---

### Tool 5 — `summarize_topics`
Condenses verbose, unstructured discussion notes into professional CRM language. Rewrites raw text into the kind of clean summary a CRM record should contain.

**Try it:** First log a verbose interaction, then:
```
Summarize the topics discussed
```

---

## Project Structure

```
hcp-crm/
│
├── frontend/                        # React application
│   ├── src/
│   │   ├── store/
│   │   │   ├── store.js             # Redux store configuration
│   │   │   ├── formSlice.js         # Form state — applyAIUpdates / applyEditUpdates
│   │   │   └── chatSlice.js         # Chat history, loading, session state
│   │   ├── components/
│   │   │   ├── InteractionForm.jsx  # Left panel — all form fields, read from Redux
│   │   │   ├── AIAssistant.jsx      # Right panel — chat UI, API calls, dispatches
│   │   │   └── ChatMessage.jsx      # Individual message bubble component
│   │   ├── hooks/
│   │   │   └── useAPI.js            # Axios instance + all API call functions
│   │   ├── App.jsx                  # Root layout — topbar + split layout
│   │   ├── main.jsx                 # React entry point with Redux Provider
│   │   └── index.css                # All styles — CSS variables, layout, components
│   ├── .env.example
│   ├── vercel.json                  # Vercel deployment config
│   └── package.json
│
├── backend/                         # FastAPI + LangGraph application
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, startup, route registration
│   │   ├── config.py                # Pydantic-settings — reads from .env
│   │   ├── agent/
│   │   │   ├── tools.py             # All 5 LangGraph @tool functions + Groq LLM
│   │   │   └── graph.py             # StateGraph, intent detection, run_agent()
│   │   ├── models/
│   │   │   ├── interaction.py       # SQLAlchemy — Interaction + HCP tables
│   │   │   └── schemas.py           # Pydantic — request/response validation
│   │   ├── db/
│   │   │   └── database.py          # SQLAlchemy engine, session, init_db()
│   │   └── routes/
│   │       └── interactions.py      # All API endpoints
│   ├── requirements.txt
│   ├── railway.toml                 # Railway deployment config
│   ├── .python-version              # Python 3.11
│   └── .env.example
│
└── README.md
```

---

## Running Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL database (local or Railway)
- Groq API key — free at [console.groq.com](https://console.groq.com)

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/hcp-crm.git
cd hcp-crm
```

### 2. Backend setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/hcp_crm
FRONTEND_URL=http://localhost:5173
```

Start the server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be live at `http://localhost:8000`  
Auto-generated docs at `http://localhost:8000/docs`

### 3. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_URL=http://localhost:8000/api
```

Start the dev server:
```bash
npm run dev
```

Open `http://localhost:5173`

### 4. Seed demo HCP data (optional but recommended)

```bash
curl -X POST http://localhost:8000/api/hcps/seed
```

This adds 8 sample HCPs (Dr. Sarah Smith, Dr. Priya Patel, etc.) for the search tool to use.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send message to LangGraph agent, receive form updates + AI response |
| `POST` | `/api/interactions` | Save finalized interaction record to PostgreSQL |
| `GET` | `/api/interactions` | Fetch 20 most recent saved interactions |
| `GET` | `/api/hcps/search?q=` | Fuzzy search HCP records by name |
| `POST` | `/api/hcps/seed` | Seed 8 demo HCP records |
| `GET` | `/api/health` | Health check |

### Chat request/response shape

```json
// POST /api/chat
{
  "message": "Today I met Dr. Smith...",
  "form_state": { "hcp_name": null, "sentiment": "neutral", ... },
  "chat_history": [{ "role": "user", "content": "..." }],
  "session_id": "uuid-optional"
}

// Response
{
  "assistant_message": "✅ Interaction logged!\n\n👤 Dr. Smith | 📅 2026-05-21 | ...",
  "form_updates": { "hcp_name": "Dr. Smith", "sentiment": "positive", ... },
  "suggestions": ["Schedule follow-up in 2 weeks", "Send efficacy PDF"],
  "action_type": "log_interaction",
  "session_id": "uuid"
}
```

---

## Deployment

### Backend → Railway

1. Push `backend/` folder to a GitHub repo
2. Create new Railway project → Deploy from GitHub
3. Add PostgreSQL plugin to the project
4. Set environment variables in Railway dashboard:

| Variable | Value |
|---|---|
| `GROQ_API_KEY` | Your Groq API key |
| `DATABASE_URL` | Auto-filled by Railway PostgreSQL plugin |
| `FRONTEND_URL` | Your Vercel frontend URL |

Railway uses `railway.toml` for the start command automatically.

### Frontend → Vercel

1. Push `frontend/` folder to GitHub
2. Import project on [vercel.com](https://vercel.com)
3. Set environment variable:

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://your-backend.railway.app/api` |

`vercel.json` handles SPA routing automatically.

---

## Database Schema

### `interactions` table
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `hcp_name` | VARCHAR | Healthcare Professional name |
| `interaction_type` | VARCHAR | Meeting / Call / Email / Conference / Other |
| `date` | VARCHAR | Interaction date (YYYY-MM-DD) |
| `time` | VARCHAR | Interaction time (HH:MM) |
| `attendees` | TEXT | Other attendees |
| `topics_discussed` | TEXT | AI-summarized discussion topics |
| `materials_shared` | JSON | Array of shared materials |
| `samples_distributed` | JSON | Array of distributed samples |
| `sentiment` | VARCHAR | positive / neutral / negative |
| `outcomes` | TEXT | Professional CRM outcome summary |
| `follow_up_actions` | TEXT | Next steps |
| `ai_suggested_followups` | JSON | Array of AI-generated suggestions |
| `raw_chat_log` | JSON | Full conversation history |
| `created_at` | TIMESTAMP | Record creation time |

### `hcps` table
| Column | Type | Description |
|---|---|---|
| `id` | UUID | Primary key |
| `name` | VARCHAR | Full name with title |
| `specialty` | VARCHAR | Medical specialty |
| `hospital` | VARCHAR | Affiliated hospital |

---

## Key Engineering Decisions

**Why LangGraph over a simple LLM call?**  
LangGraph gives us a stateful, inspectable agent with explicit tool routing. Each tool has a single responsibility. The graph makes the orchestration logic visible and testable — not buried in a prompt.

**Why `tools → END` instead of `tools → agent`?**  
Chaining tool calls through the graph doubles LLM latency. With Groq's free tier, two sequential calls reliably timeout at 30s. `suggest_followups` runs inline in Python after `log_interaction` returns — same result, one round trip.

**Why two Redux actions (`applyAIUpdates` vs `applyEditUpdates`)?**  
`log_interaction` should update all non-null fields. `edit_interaction` should only touch the exact fields returned — nothing else. A single apply function can't distinguish these cases cleanly. Splitting them prevents a `"change the time"` request from accidentally resetting sentiment or clearing materials.

**Why does the edit prompt say "NEVER include sentiment unless user explicitly says sentiment"?**  
LLMs naturally re-infer sentiment from context. Without this explicit constraint, editing the outcomes field would cause the LLM to re-evaluate the whole message and quietly change sentiment. The hard prohibition in the prompt prevents this.

---

## Author

**Abhishek** — MCA (AI), Jain University  
Backend Developer Intern @ ComixCanal  
