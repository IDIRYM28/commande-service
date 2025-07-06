import os
import sys
import pathlib
import pytest
import importlib.util
import types

# Determine project root (clients-service directory)
project_root = pathlib.Path(__file__).parent.parent.resolve()
# Add project root to sys.path to import app package
sys.path.insert(0, str(project_root))

# Create a dynamic package 'app' if not a real package
app_pkg = types.ModuleType("app")
app_pkg.__path__ = [str(project_root / "app")]
sys.modules["app"] = app_pkg

# Dynamically load all modules under app/
MODULES = ["database", "models", "schemas", "crud", "main"]
for name in MODULES:
    module_path = project_root / "app" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"app.{name}", str(module_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[f"app.{name}"] = module
    setattr(app_pkg, name, module)

from app.main import app as fastapi_app
from fastapi.testclient import TestClient

# Shared TestClient for API tests
client = TestClient(fastapi_app)

@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch):
    """
    Override DB, authentication and messaging for isolated testing.
    """
    # ── override de app.database pour un in-memory partagé ──
    import app.database as db_mod
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    # on recrée un engine SQLite in-memory qui partage le même cache
    shared_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )

    # 2) Réassigner engine et SessionLocal dans app.database
    db_mod.engine = shared_engine
    db_mod.SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=shared_engine
    )
    # 3) Créer les tables UNE SEULE FOIS pour toute la session de tests

    # ── création des tables sur ce nouvel engine ──
    from app.database import Base
    Base.metadata.create_all(bind=shared_engine)
    session = db_mod.SessionLocal()
    # Importer les modèles
    from app import models
    session.add_all([
        models.Client(name="ClientOne", email="one@example.com"),
        models.Client(name="ClientTwo", email="two@example.com"),
        models.Product(name="ProductOne", price=15.0),
        models.Product(name="ProductTwo", price=25.0),
    ])
    session.commit()
    session.close()
    def get_db_override():
        db = db_mod.SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Patch get_db and get_current_user in main module
    import app.main as main_mod
    fastapi_app.dependency_overrides[main_mod.get_db] = get_db_override


    # Disable messaging publish
