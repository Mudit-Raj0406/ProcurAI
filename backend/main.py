from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from database import engine, Base
from routers import quotes, auth

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ProcurAI - Intelligent Procurement Assistant")

# CORS Configuration
origins = [
    "*",
]

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
