from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import time
import os

# Database connection URL - defaults to local PostgreSQL if not set
DATABASE_URL = os.getenv("DATABASE_URL")

# Retry logic for database connection
# This is useful in Docker environments where the database might not be ready immediately
# The healthcheck in docker-compose.yml ensures the database is ready before the app starts
for _ in range(10):
    try:
        # Create SQLAlchemy engine with the database URL
        engine = create_engine(DATABASE_URL)
        break
    except Exception:
        print("Waiting for DB...")
        time.sleep(3)

# Create session factory for database operations
# autocommit=False: Changes are not automatically committed
# autoflush=False: Changes are not automatically flushed to the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for SQLAlchemy models
# All models will inherit from this Base class
Base = declarative_base()
