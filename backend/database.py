# backend/database.py

import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1) Charge le .env (même si tu lances depuis un sous-dossier)
load_dotenv(find_dotenv())

# 2) Récupère les variables avec fallback
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "db")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "olap_db")

# 3) Construit l’URL de connexion
DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}"
    f":{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}"
    f":{POSTGRES_PORT}"
    f"/{POSTGRES_DB}"
)

# 4) Crée le moteur SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
print(f"🔗 Connexion à la base de données : {DATABASE_URL}")

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
metadata = MetaData()
Base = declarative_base()


# 5) Dépendance FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
