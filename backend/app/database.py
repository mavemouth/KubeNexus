import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load environment variables from backend/.env or root .env
load_dotenv()
backend_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Supabase and PostgreSQL compatibility:
# SQLAlchemy 2.0 requires "postgresql://" or "postgresql+psycopg2://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = False

if DATABASE_URL:
    print(f"[Database] Connecting to PostgreSQL / Supabase...")
    # Add connect_args if using postgres to ensure SSL if required
    connect_args = {}
    if "supabase.co" in DATABASE_URL or "sslmode" not in DATABASE_URL:
        # Supabase requires SSL or handles it via standard sslmode
        pass

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False
    )
else:
    # Safe local fallback when user has not yet configured Supabase
    is_sqlite = True
    local_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kubenexus.db")
    fallback_url = f"sqlite:///{local_db_path}"
    print("[Database] Warning: No DATABASE_URL set.")
    print("           Running on local SQLite fallback until Supabase DATABASE_URL is added to backend/.env")
    engine = create_engine(
        fallback_url,
        connect_args={"check_same_thread": False},
        echo=False
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """FastAPI dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes schema and tables if they don't already exist"""
    try:
        from app.models import orm  # noqa: F401
        Base.metadata.create_all(bind=engine)
        print("[Database] Schema synchronized successfully.")
    except Exception as e:
        print(f"[Database] Warning: Schema initialization check encountered: {e}")
