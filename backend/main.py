import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password, verify_password
from coordinator_agent import classify_concern
from database import Base, engine, get_db
from db_models import Consultation, User
from logging_config import logger
from schemas import ConsultationOut, Token, UserCreate, UserLogin, UserOut
from specialists import get_specialist_response
from voice_of_patient import transcribe_patient_voice
from voice_of_specialist import AUDIO_OUTPUT_DIR, convert_text_to_speech

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Hair & Skin Specialist API")

FRONTEND_ORIGINS = os.environ.get(
    "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(AUDIO_OUTPUT_DIR)), name="audio")

UPLOAD_DIR = Path(tempfile.gettempdir()) / "hair_skin_specialist_uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ---------- Auth ----------

@app.post("/api/auth/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered | email=%s", user.email)

    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@app.post("/api/auth/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        logger.warning("Failed login attempt | email=%s", payload.email)
        raise HTTPException(status_code=401, detail="Incorrect email or password.")

    logger.info("User logged in | email=%s", user.email)
    token = create_access_token(subject=user.id)
    return Token(access_token=token, user=UserOut.model_validate(user))


@app.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user


# ---------- Consultation ----------

def _save_upload(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix
    dest = UPLOAD_DIR / f"{uuid.uuid4().hex}{suffix}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return str(dest)


@app.post("/api/consult", response_model=ConsultationOut)
async def consult(
    audio: UploadFile = File(...),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if image is None and video is None:
        raise HTTPException(status_code=400, detail="Please provide an image or video.")

    start_time = time.perf_counter()

    audio_path = _save_upload(audio)
    image_path = _save_upload(image) if image is not None else None
    video_path = _save_upload(video) if video is not None else None

    try:
        transcript = transcribe_patient_voice(audio_path)

        # The coordinator decides the specialty independent of which
        # frontend page (skin or hair) the request came from.
        specialty = classify_concern(transcript)

        specialist_text = get_specialist_response(
            specialty=specialty,
            patient_text=transcript,
            image_filepath=image_path,
            video_filepath=video_path,
        )
        audio_file_path = convert_text_to_speech(specialist_text)
        audio_filename = Path(audio_file_path).name

        latency_ms = (time.perf_counter() - start_time) * 1000

        record = Consultation(
            user_id=current_user.id,
            specialty=specialty,
            transcript=transcript,
            specialist_response=specialist_text,
            audio_filename=audio_filename,
            latency_ms=latency_ms,
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        logger.info(
            "Consultation OK | user=%s | specialty=%s | latency_ms=%.0f",
            current_user.email, specialty, latency_ms,
        )

        return ConsultationOut(
            id=record.id,
            specialty=record.specialty,
            transcript=record.transcript,
            specialist_response=record.specialist_response,
            audio_url=f"/audio/{audio_filename}",
            latency_ms=record.latency_ms,
            created_at=record.created_at,
        )
    except ValueError as e:
        logger.warning("Consultation failed (bad input) | user=%s | error=%s", current_user.email, e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Consultation failed | user=%s | error=%s", current_user.email, e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        for p in (audio_path, image_path, video_path):
            if p and os.path.exists(p):
                os.remove(p)


@app.get("/api/history", response_model=List[ConsultationOut])
def history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = (
        db.query(Consultation)
        .filter(Consultation.user_id == current_user.id)
        .order_by(Consultation.created_at.desc())
        .all()
    )
    return [
        ConsultationOut(
            id=r.id,
            specialty=r.specialty,
            transcript=r.transcript,
            specialist_response=r.specialist_response,
            audio_url=f"/audio/{r.audio_filename}" if r.audio_filename else None,
            latency_ms=r.latency_ms,
            created_at=r.created_at,
        )
        for r in records
    ]


@app.get("/api/health")
def health():
    return {"status": "ok"}
