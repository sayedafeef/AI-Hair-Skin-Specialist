# AI Hair & Skin Specialist

A two-page telehealth-style app with a coordinator agent that automatically
routes each consultation to a skin or hair specialist model, regardless of
which page the request came from. Consultations are tied to a logged-in
account, persisted in a database, and every request is logged server-side.

## Architecture

- **Backend** (`backend/`): FastAPI.
  - `POST /api/consult` accepts a voice recording plus an optional image/video,
    transcribes the voice with Groq Whisper, classifies the concern with a
    lightweight coordinator agent (`openai/gpt-oss-20b`), routes it to the
    matching specialist prompt on a vision-capable model (`qwen/qwen3.8-27b`),
    and synthesizes the specialist's reply to speech with Deepgram.
  - `POST /api/auth/register` / `POST /api/auth/login` issue a JWT.
  - `GET /api/history` returns the logged-in user's past consultations.
  - Every consultation is saved to a SQLite database (`backend/app.db`) via
    SQLAlchemy, and every request is logged to console + a rotating file
    under `backend/logs/app.log`.
- **Frontend** (`frontend/`): React + Vite. Login/register page, two
  consultation pages (`/` for skin, `/hair` for hair) gated behind auth, and
  a `/history` page showing past consultations. Records audio in the browser
  with the MediaRecorder API and uploads it directly - Groq's Whisper
  endpoint accepts webm natively, no conversion needed.

## Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux
```

Fill in `backend/.env`:

```
GROQ_API_KEY=...
DEEPGRAM_API_KEY=...
SECRET_KEY=...   # generate with: python -c "import secrets; print(secrets.token_hex(32))"
```

`DATABASE_URL` can be left blank to use a local SQLite file
(`backend/app.db`), created automatically on first run. To use Postgres
instead, set it to something like
`postgresql://user:password@localhost:5432/dbname` and
`pip install psycopg2-binary`.

Run the API:

```bash
uvicorn main:app --reload --port 8000
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL Vite prints (typically `http://localhost:5173`). You'll land
on the login page first - create an account, then use the app.

## What's new in this version

- **Storage**: consultations (transcript, specialist response, audio
  filename, latency, timestamp) are persisted in SQLite via SQLAlchemy,
  scoped to the account that created them.
- **Login**: JWT-based auth. Passwords are hashed with bcrypt
  (`passlib`), tokens are signed with `SECRET_KEY` and expire after
  `ACCESS_TOKEN_EXPIRE_MINUTES` (default 24h). `/api/consult` and
  `/api/history` require a valid bearer token.
- **Logs**: two layers -
  1. Server-side application logs (`backend/logs/app.log`, rotating at
     ~2MB, 3 backups kept) recording registrations, logins, and every
     consultation attempt with its outcome and latency.
  2. A user-facing `/history` page, backed by the same database, showing
     each account's own past consultations.

## Notes

- The backend writes generated speech to `backend/generated_audio/` with
  unique filenames per request and serves them at `/audio/<file>.mp3`.
  History playback depends on these files staying in place - add a
  retention/cleanup policy before deploying this beyond local development.
- CORS is restricted to `http://localhost:5173` and `http://127.0.0.1:5173`
  by default; adjust `FRONTEND_ORIGINS` in `.env` if you host the frontend
  elsewhere.
- The coordinator agent defaults to `skin` if its classification call ever
  fails to parse, so a routing hiccup never breaks the consultation.
- `SECRET_KEY` must stay secret and stable - rotating it invalidates every
  issued token, logging everyone out.
