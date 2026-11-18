# pyright: reportMissingImports=false
# pyright: reportPossiblyUnboundVariable=false
# pyright: reportUnusedVariable=false
import os
import tempfile
from typing import Any
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# Load environment variables from backend/.env or root .env
load_dotenv()
backend_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(backend_env_path):
    load_dotenv(backend_env_path)

DATABASE_URL = os.getenv("DATABASE_URL", "").strip().strip("'\"")

# Supabase / PostgreSQL compatibility:
# SQLAlchemy 2.0 requires "postgresql://", "postgresql+psycopg2://", or "postgresql+psycopg://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = False
engine: Any = None

if DATABASE_URL:
    print("[Database] Initializing PostgreSQL / Supabase connection...")

    # Supabase Transaction Pooler (PgBouncer port 6543) configuration:
    # 1. SSL is mandatory for Supabase
    # 2. Connection timeout set to 10 seconds to avoid hanging
    connect_args: dict[str, Any] = {
        "connect_timeout": 10,
    }
    if "supabase.co" in DATABASE_URL or "pooler.supabase.com" in DATABASE_URL or "sslmode" not in DATABASE_URL:
        connect_args["sslmode"] = "require"

    engine_kwargs: dict[str, Any] = {
        "connect_args": connect_args,
        "echo": False,
    }

    # In serverless environments (Vercel Functions), NullPool avoids connection exhaustion
    if os.getenv("VERCEL"):
        engine_kwargs["poolclass"] = NullPool
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 300

    connected = False
    candidate_urls = [DATABASE_URL]

    # Generate fallback driver candidates if URL specifies or implies a specific driver
    if "+psycopg2" in DATABASE_URL:
        candidate_urls.append(DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1))
    elif "+psycopg" in DATABASE_URL:
        candidate_urls.append(DATABASE_URL.replace("postgresql+psycopg://", "postgresql+psycopg2://", 1))
    elif DATABASE_URL.startswith("postgresql://"):
        candidate_urls.append(DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1))
        candidate_urls.append(DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1))

    last_exc = None
    for url_attempt in candidate_urls:
        try:
            temp_engine = create_engine(url_attempt, **engine_kwargs)
            # Test connection actively
            with temp_engine.connect():
                pass
            engine = temp_engine
            DATABASE_URL = url_attempt
            connected = True
            print("[Database] Connected to PostgreSQL / Supabase successfully.")
            break
        except Exception as exc:
            last_exc = exc
            # If error is not driver-related (e.g. auth failed or host unreachable), don't try alternate driver loops
            err_str = str(exc).lower()
            if "no module named" not in err_str and "driver" not in err_str:
                break

    if not connected:
        # Sanitize exception message so database credentials are never leaked in logs
        raw_exc = str(last_exc) if last_exc else "Unknown error"
        if "@" in raw_exc:
            safe_msg = raw_exc.split("@")[-1]
        else:
            safe_msg = raw_exc
        print(f"[Database] Warning: Failed to connect to PostgreSQL ({safe_msg}).")
        print("           Falling back to local SQLite database (kubenexus.db).")
        is_sqlite = True
        if os.getenv("VERCEL"):
            local_db_path = os.path.join(tempfile.gettempdir(), "kubenexus.db")
        else:
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
    if os.getenv("VERCEL"):
        local_db_path = os.path.join(tempfile.gettempdir(), "kubenexus.db")
    else:
        local_db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "kubenexus.db")
    fallback_url = f"sqlite:///{local_db_path}"
    print(f"[Database] Running on local SQLite fallback ({local_db_path})")
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

        # Ensure newly added columns exist in existing schemas
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
                        VALUES (1, 20.0, 7, 'High', 'http://prometheus.monitoring.svc.cluster.local:9090', 30, true, true, '/api/v1')
                    """))
                    conn.commit()

        print("[Database] Schema synchronized successfully.")
    except Exception as e:
        print(f"[Database] Warning: Schema initialization check encountered: {e}")
