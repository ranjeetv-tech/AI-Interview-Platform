# InterviewAI — Your Personal AI Interviewer

InterviewAI is a local-first spoken interview simulator for software, AI and ML placement preparation. It uses a Next.js/React/TypeScript frontend, FastAPI backend, SQLite/SQLAlchemy persistence, browser speech APIs, and an interchangeable LLM layer for Ollama or an OpenAI-compatible API.

## What is implemented

- Resume upload for PDF/DOCX with real text extraction and structured profile analysis.
- Demo candidate profile for immediate testing.
- Optional JD analysis and resume/JD-aware interview context.
- Role, interview type, difficulty and 10/20/30-minute configuration.
- Adaptive question generation based on profile, role, JD, previous questions and answers.
- Project deep-dive capable of progressively probing architecture, algorithms, choices, trade-offs, limitations and scaling.
- Structured answer analysis and follow-up decisions.
- Browser microphone speech recognition and browser text-to-speech with explicit voice states.
- Interrupt/repeat controls and graceful microphone/AI errors.
- SQLAlchemy models for candidates, resumes, interviews, questions, answers and feedback.
- Deterministic weighted scoring: Communication 20%, Technical 25%, Projects 20%, Problem Solving 15%, Behavioral 10%, Delivery 10%.
- Evidence-based final report, category breakdown, strengths, weaknesses, Fix This First, question review and personalized study plan.
- Interview history and dashboard trend data.
- Automated backend tests for scoring and upload filename safety.

## Architecture

```text
Browser (Next.js)
   ├── Web Speech API (STT/TTS)
   ↓
FastAPI
   ├── Resume/JD services
   ├── Interview state + adaptive orchestration
   ├── AI provider abstraction ── Ollama / OpenAI-compatible
   └── SQLAlchemy ── SQLite
```

Speech provider-specific logic is isolated in the browser-side speech flow and backend speech abstraction so another provider can be introduced later.

## Requirements — Windows 10/11

- Python 3.11+ (3.12 recommended)
- Node.js 20+
- VS Code
- Chrome or Edge recommended for Web Speech API support
- Optional: Ollama for local AI

## Windows installation

Open the project in VS Code. Use two terminals.

### Backend

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy ..\.env.example .env
uvicorn app.main:app --reload --port 8000
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### Frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Environment variables

The backend reads `.env` from `backend/` when started from the `backend` directory.

```text
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=sqlite:///./interviewai.db
FRONTEND_ORIGIN=http://localhost:3000
MAX_UPLOAD_MB=8
UPLOAD_DIR=./uploads
```

No API key is sent to the frontend.

## Local AI with Ollama

Install Ollama for Windows, start it, then pull a model suitable for your hardware. For example:

```powershell
ollama pull llama3.2
```

Keep `LLM_PROVIDER=ollama`. If the selected model is different, change `LLM_MODEL`.

The browser still performs speech recognition/text-to-speech; the LLM and database can remain local.

## OpenAI-compatible API

Set:

```text
LLM_PROVIDER=openai
LLM_MODEL=your-model-name
OPENAI_API_KEY=your-key
OPENAI_BASE_URL=https://api.openai.com/v1
```

Any compatible endpoint that supports `/chat/completions` and JSON response format can be used by changing `OPENAI_BASE_URL`.

## Speech

InterviewAI uses browser speech capabilities to avoid requiring a separate paid speech service. Chrome/Edge is recommended. The app handles denied permissions, unavailable recognition, empty answers and recognition failures by allowing the transcript to be edited manually.

## Database

SQLite is created automatically as `interviewai.db` in the backend working directory. The SQLAlchemy model layer keeps the persistence code database-agnostic enough to migrate to PostgreSQL later.

## API

- `POST /api/resume/upload`
- `POST /api/resume/demo`
- `POST /api/interviews`
- `GET /api/interviews`
- `GET /api/interviews/{id}`
- `POST /api/interviews/{id}/start`
- `POST /api/interviews/{id}/answer`
- `POST /api/interviews/{id}/next-question`
- `POST /api/interviews/{id}/complete`
- `GET /api/interviews/{id}/feedback`
- `DELETE /api/interviews/{id}`
- `GET /api/dashboard`

## Testing

From `backend`:

```powershell
py -m pytest -q
```

The tests cover deterministic scoring/classification and filename sanitization. The application also validates AI JSON before consuming it and returns controlled HTTP errors for failed AI operations.

## Troubleshooting

**`ModuleNotFoundError`** — activate the backend virtual environment and run `pip install -r requirements.txt`.

**Frontend cannot reach API** — verify FastAPI is running on port 8000. If needed, create `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000/api`.

**Ollama connection error** — verify Ollama is running and the configured model exists with `ollama list`.

**Microphone denied** — allow microphone access for `localhost` in the browser site permissions, then reload.

**Speech recognition unavailable** — use Chrome/Edge or type/edit the transcript manually.

**Resume parsing error** — make sure the file is a valid PDF/DOCX with selectable/extractable text and is under the configured size limit.

## Project structure

```text
interview-ai/
├── frontend/
│   ├── app/                 # pages and interview flow
│   ├── components/          # UI and charts
│   ├── lib/api.ts           # backend client
│   └── types/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routes
│   │   ├── ai/              # provider abstraction
│   │   ├── database/        # SQLAlchemy setup
│   │   ├── models/          # database entities
│   │   ├── prompts/         # dedicated AI prompts
│   │   ├── schemas/         # Pydantic contracts
│   │   ├── services/        # orchestration/scoring
│   │   ├── speech/          # speech provider abstraction
│   │   └── utils/           # document parsing/security helpers
│   └── tests/
├── .env.example
├── docker-compose.yml
└── README.md
```

## Limitations

- Browser speech recognition availability and quality depend on the browser/OS and language environment.
- LLM feedback is AI-assisted assessment, not an objective substitute for a human interviewer.
- Delivery scoring uses observable transcript characteristics such as filler-word occurrences and response length; it does not infer psychological traits.
- The current implementation is intentionally single-user/local-first and does not include authentication or multi-user tenancy.
- The adaptive engine is LLM-driven, so question quality depends on the configured model.

## Future improvements

Streaming audio, a dedicated local STT model such as Whisper, richer audio analytics, authentication, PostgreSQL, multi-session user accounts, question-bank analytics, and deployment-specific observability can be added without changing the core interview orchestration contracts.
