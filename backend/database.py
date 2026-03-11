import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Fix for SQLAlchemy 1.4+ which dropped support for the 'postgres://' URI scheme
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    # Supabase/Cloud PostgreSQL requires SSL. Append if not present.
    if "postgresql://" in DATABASE_URL and "?" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    elif "postgresql://" in DATABASE_URL and "sslmode=" not in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"
        
    engine = create_engine(DATABASE_URL)
else:
    # Fallback to local SQLite if no remote database is configured
    SQLALCHEMY_DATABASE_URL = "sqlite:///./procurai_v2.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 30}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
