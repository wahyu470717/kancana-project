from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import os

def get_database_url():

    
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        print("Using DATABASE_URL from environment (Supabase)")
        # Pastikan ada SSL mode
        if "sslmode" not in database_url:
            database_url += "?sslmode=require"
        return database_url
    
    DB_USER = settings.DB_USER        # postgres
    DB_PASS = settings.DB_PASS        # wahyu260697
    DB_HOST = settings.DB_HOST        # localhost
    DB_PORT = settings.DB_PORT        # 5432
    DB_NAME = settings.DB_NAME        # monitoring_jalan
    
    return f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SQLALCHEMY_DATABASE_URL = get_database_url()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=0,
    pool_recycle=300,
    echo=False,
    connect_args={
        "sslmode": "require"
    } if "supabase" in SQLALCHEMY_DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

        