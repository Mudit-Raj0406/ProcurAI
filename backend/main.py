import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from database import engine, Base
from routers import quotes, auth

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ProcurAI - Intelligent Procurement Assistant")

# CORS Configuration
# Allow explicit frontend origins for credential-based requests
default_origins = "http://localhost:3000,http://127.0.0.1:3000,https://procur-ai-frontend.vercel.app"
origins = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", default_origins).split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes.router)
app.include_router(auth.router)

@app.get("/health")
def health_check():
    return {"status": "ok", "message": "ProcurAI Backend is running"}

@app.get("/")
def root():
    return RedirectResponse(url="/docs")
