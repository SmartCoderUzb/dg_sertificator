import os
import secrets
from datetime import date
from typing import Optional
from uuid import uuid4, UUID

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import (
    Column, Integer, String, Date, create_engine, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from dotenv import load_dotenv

# =========================
# Config
# =========================

load_dotenv()

DB_URL = os.getenv("DB_URL", "sqlite:///./data.db")
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "wM732s]WM5MJ")

print(ADMIN_USER, ADMIN_PASS)
engine = create_engine(DB_URL, connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

Base = declarative_base()
app = FastAPI(
    title="Dj sertificator API", 
    version="1.0.0", 
    docs_url="/izzatillo_v1_docs/",
    debug=False,
    openapi_url="/jsonfile_v1.json"    
)

templates = Jinja2Templates(directory="templates")

security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username, ADMIN_USER)
    correct_pass = secrets.compare_digest(credentials.password, ADMIN_PASS)
    if not (correct_user and correct_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# DB Model
# =========================
class Person(Base):
    __tablename__ = "people"

    id = Column(
        String(100), 
        primary_key=True, 
        default=lambda: str(uuid4()), 
        unique=True, 
        nullable=False
    )

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100), nullable=True)

    parents_phone = Column(String(200), nullable=True)

    viloyat = Column(String(120), nullable=True)
    tuman = Column(String(120), nullable=True)
    manzil = Column(String(255), nullable=True)

    yonalish = Column(String(200), nullable=True)
    about_me = Column(Text, nullable=True)
    oqigan_joyi = Column(String(200), nullable=True)

    tugilgan_kun = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    tg_username = Column(String(100), nullable=True)
    email = Column(String(200), nullable=True)        # email

# Create tables on startup
Base.metadata.create_all(bind=engine)

# =========================
# Schemas (Pydantic)
# =========================
class PersonCreate(BaseModel):
    first_name: str = Field(..., description="ism")
    last_name: str = Field(..., description="familiya")
    middle_name: Optional[str] = Field(None, description="otasini ismi")

    parents_phone: Optional[str] = Field(None, description="ota + ona tel")

    viloyat: Optional[str] = Field(None, description="vil")
    tuman: Optional[str] = Field(None, description="tum")
    manzil: Optional[str] = Field(None, description="manzil")

    yonalish: Optional[str] = Field(None, description="yo'nalish")
    about_me: Optional[str] = Field(None, description="about me")
    oqigan_joyi: Optional[str] = Field(None, description="o‘qigan joyi")

    tugilgan_kun: Optional[date] = Field(None, description="t kun (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, description="gender")
    tg_username: Optional[str] = Field(None, description="tg username (e.g. @fayzullo)")
    email: Optional[EmailStr] = Field(None, description="email")

class PersonOut(PersonCreate):
    id: str

    class Config:
        from_attributes = True  # Pydantic v2 compatible (ORM mode)

# =========================
# Routes
# =========================
@app.post("/api/students", response_model=PersonOut, status_code=201)
def create_person(payload: PersonCreate, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    person = Person(**payload.dict())
    db.add(person)
    db.commit()
    db.refresh(person)
    return person

@app.get("/api/students/{person_id}", response_model=PersonOut)
def get_person(person_id: int, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Not found")
    return person

@app.get("/students/{person_id}", response_class=HTMLResponse)
def person_detail_page(person_id: int, request: Request, _: str = Depends(require_auth), db: Session = Depends(get_db)):
    person = db.get(Person, person_id)
    if not person:
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse("detail.html", {"request": request, "p": person})
