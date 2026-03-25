# MoveWise

**AI-powered relocation decision assistant.** Compare any two addresses across safety, cost of living, noise, lifestyle, and commute — then ask an AI advisor to help you decide.

**Live:** [movewise-web.vercel.app](https://movewise-web.vercel.app)

---

## What It Does

MoveWise lets you run a data-driven analysis on any move you're considering. Enter your current address and a destination — MoveWise pulls real data across five dimensions and gives each a score:

| Dimension | Data Source | What It Measures |
|---|---|---|
| **Safety** | Government crime statistics | Crime rate vs. national average |
| **Affordability** | 2024 cost-of-living data | Monthly expenses vs. your current location |
| **Noise / Environment** | Noise level data | How quiet or loud the area is vs. your preference |
| **Lifestyle** | Nearby amenities | How many places match your hobbies |
| **Convenience** | Mapping & directions data | Commute time to your work address |

These combine into an **Overall Score (0–100)** with a letter grade (A+ to D). An AI-written narrative explains what the move would actually mean for your day-to-day life.

---

## Features

### Analysis Engine
- Runs entirely in the background — submit and return to the dashboard instantly
- Real-time status updates via server-sent events (no page refresh needed)
- Parallel data fetching for all five dimensions
- Personalized scores based on your profile (work hours, commute mode, sleep schedule, hobbies)
- AI-generated overview, lifestyle change summary, and action steps

### AI Chat Advisor
- Persistent chat widget across all pages — history survives navigation
- Tool-calling agent (up to 5 reasoning rounds) with four analysis tools:
  - Fetch full details for any analysis
  - Compare two or more destinations side by side
  - Rank all analyses by any factor (safety, affordability, commute, etc.)
  - Filter analyses by location keywords
- **RAG knowledge base** — 30 help-center chunks embedded with Cohere and stored in pgvector. The agent retrieves relevant content via cosine similarity to answer how-to and navigation questions without exposing internal system details

### Profile Personalization
- 3-step setup wizard: work schedule, sleep & noise preferences, hobbies
- Commute preference (driving, transit, bicycling, walking) or work-from-home toggle
- Profile changes apply to all future analyses

### Auth & Security
- Cookie-based JWT authentication (httpOnly, secure in production)
- No tokens in localStorage

---

## Tech Stack

**Frontend**
- React + TypeScript (Vite)
- Tailwind CSS
- Zustand (auth, analyses, chat — all in-memory except auth persistence)
- React Router

**Backend**
- FastAPI + SQLAlchemy
- PostgreSQL (Neon) with pgvector extension
- Redis (Upstash) for SSE pub/sub
- Background tasks via FastAPI `BackgroundTasks`

**AI / ML**
- Groq `llama-3.3-70b-versatile` — chat agent + analysis narrative generation
- Cohere `embed-english-v3.0` — RAG document embeddings (1024-dim)
- pgvector HNSW index — cosine similarity retrieval

**External APIs**
- Google Maps Platform (Geocoding, Places, Directions)
- FBI Crime Data Explorer
- HowLoud SoundScore API

**Deployment**
- Frontend: [Vercel](https://vercel.com)
- Backend: [Render](https://render.com)

---

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL database (or a [Neon](https://neon.tech) project)
- Redis instance (or [Upstash](https://upstash.com))

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
DATABASE_URL=postgresql://...
SECRET_KEY=your-secret-key
GROQ_API_KEY=...
GOOGLE_MAPS_API_KEY=...
COHERE_API_KEY=...
REDIS_URL=rediss://...
ENVIRONMENT=development
```

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. On first startup, it automatically:
- Enables the `pgvector` extension in your database
- Creates all tables
- Seeds the RAG knowledge base (30 chunks, idempotent)

### Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

```bash
npm run dev
```

---

## Project Structure

```
MoveWise-Web/
├── frontend/
│   └── src/
│       ├── pages/          # Dashboard, LocationInput, ProfileSetup, AnalysisDetailPage, ...
│       ├── components/     # DashboardChat, ProtectedRoute, ...
│       └── stores/         # authStore, analysisStore, chatStore
└── backend/
    └── app/
        ├── api/            # auth, profile, analysis, chat, stream
        ├── models/         # User, UserProfile, Analysis, DocChunk
        ├── services/       # chat_service, llm_service, scoring_service,
        │                   # embedding_service, rag_seeder, crime/cost/noise/places
        ├── tasks/          # analysis_tasks (background pipeline)
        └── core/           # config, database, security
```
