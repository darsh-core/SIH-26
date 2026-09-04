import os
import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Set default test environment for providers
os.environ["AI_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "mock"

from app.core.config import settings
from app.core.database import Base
settings.AI_PROVIDER = "mock"
settings.EMBEDDING_PROVIDER = "mock"

# Force testing database URL on port 5433 (Homebrew)
TEST_DATABASE_URL = "postgresql://darshini@localhost:5433/sih_test"

@pytest.fixture(scope="session")
def db_engine():
    # Set up test engine
    engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
    
    # Ensure pgvector and uuid-ossp exist (should be enabled in init.sql, but double check)
    with engine.connect() as conn:
        conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        conn.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS "vector";')
        conn.commit()
        
    # Recreate tables in the test database
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup tables after all tests run
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    # Establish connection
    connection = db_engine.connect()
    transaction = connection.begin()
    
    # Bind session to transaction for rollbacks
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=connection
    )
    session = TestingSessionLocal()
    
    yield session
    
    # Rollback session and close connection to keep tests isolated
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
