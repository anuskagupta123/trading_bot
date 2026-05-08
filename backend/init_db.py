"""
Initialize the database and create all tables.
Run this once on first setup.
"""
from app.database.database import Base, engine
from app.database import models

def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_db()
