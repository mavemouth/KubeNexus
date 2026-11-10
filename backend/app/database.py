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
    try:
        temp_engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"connect_timeout": 5},
            echo=False
        )
        # Test connection actively
        with temp_engine.connect() as conn:
            pass
        engine = temp_engine
        print("[Database] Connected to PostgreSQL / Supabase successfully.")
    except Exception as exc:
        print(f"[Database] Warning: Failed to connect to PostgreSQL ({exc}).")
        print("           Falling back to local SQLite database (kubenexus.db).")
        is_sqlite = True
        local_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kubenexus.db")
        fallback_url = f"sqlite:///{local_db_path}"
        engine = create_engine(
            fallback_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
else:
    # Safe local fallback when user has not yet configured Supabase
    is_sqlite = True
    local_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kubenexus.db")
    fallback_url = f"sqlite:///{local_db_path}"
    print("[Database] Running on local SQLite fallback (kubenexus.db)")
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

        # Ensure newly added columns exist in existing SQLite/Postgres schemas
        from sqlalchemy import inspect, text
        inspector = inspect(engine)
        if "clusters" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("clusters")}
            with engine.connect() as conn:
                if "auth_method" not in existing_cols:
                    conn.execute(text("ALTER TABLE clusters ADD COLUMN auth_method VARCHAR(32) DEFAULT 'local'"))
                if "kubeconfig_raw" not in existing_cols:
                    conn.execute(text("ALTER TABLE clusters ADD COLUMN kubeconfig_raw TEXT"))
                if "bearer_token" not in existing_cols:
                    conn.execute(text("ALTER TABLE clusters ADD COLUMN bearer_token TEXT"))
                if "prometheus_url" not in existing_cols:
                    conn.execute(text("ALTER TABLE clusters ADD COLUMN prometheus_url VARCHAR(255) DEFAULT 'http://localhost:9090'"))
                conn.commit()

        # Ensure default settings row exists if empty
        if "settings" in inspector.get_table_names():
            with engine.connect() as conn:
                result = conn.execute(text("SELECT count(*) FROM settings")).scalar()
                if not result:
                    conn.execute(text("""
                        INSERT INTO settings (id, safety_margin_pct, min_observation_days, auto_approve_min_confidence, prometheus_url, scrape_interval_seconds, enable_hpa_safety_check, enable_vpa_conflict_check, api_base_url)
                        VALUES (1, 20.0, 7, 'High', 'http://prometheus.monitoring.svc.cluster.local:9090', 30, 1, 1, 'http://localhost:8000/api/v1')
                    """))
                    conn.commit()

        print("[Database] Schema synchronized successfully.")
    except Exception as e:
        print(f"[Database] Warning: Schema initialization check encountered: {e}")
