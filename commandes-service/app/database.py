import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv, find_dotenv

# Charger automatiquement le premier `.env` trouvé dans l'arborescence
load_dotenv(find_dotenv())

DATABASE_URL = os.getenv("ORDER_DB_URL")
if not DATABASE_URL:
    raise RuntimeError("ORDER_DB non défini dans .env")
print('data',DATABASE_URL)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()