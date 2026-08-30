import uuid
from datetime import date
from sqlalchemy.orm import Session
from app.models.user import Organization, AppUser, UserProfile, RBACRole, AuditLog
from app.models.competency import CompetencyFramework, Competency, CompetencyLevel, JobRole, RoleCompetency, UserCompetency
from app.models.document import Document, DocumentChunk, DocumentEmbedding

def test_create_organization_and_user(db_session: Session):
    # 1. Create Organization
    org = Organization(
        name="Test Census Division",
        code="TCD",
        description="Division for testing databases."
    )
    db_session.add(org)
    db_session.commit()
    assert org.id is not None
    assert isinstance(org.id, uuid.UUID)

    # 2. Create User
    user = AppUser(
        email="test_user@example.com",
        hashed_password="securepasswordhash",
        organization_id=org.id
    )
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    assert user.organization.code == "TCD"

    # 3. Create User Profile
    profile = UserProfile(
        user_id=user.id,
        first_name="Rajesh",
        last_name="Kumar",
        designation="Junior Analyst",
        department="Field Surveys",
        date_of_joining=date(2025, 1, 1)
    )
    db_session.add(profile)
    db_session.commit()
    assert profile.id is not None
    assert user.profile.first_name == "Rajesh"


def test_rbac_roles_relationship(db_session: Session):
    # 1. Create User
    user = AppUser(
        email="officer@example.com",
        hashed_password="anotherpassword"
    )
    db_session.add(user)
    
    # 2. Create Roles
    admin_role = RBACRole(name="ADMIN", description="Administrator privileges")
    official_role = RBACRole(name="OFFICIAL", description="Standard official privileges")
    db_session.add_all([admin_role, official_role])
    db_session.commit()

    # 3. Associate Roles
    user.roles.append(admin_role)
    user.roles.append(official_role)
    db_session.commit()

    # Verify relationships
    queried_user = db_session.query(AppUser).filter_by(email="officer@example.com").first()
    assert len(queried_user.roles) == 2
    role_names = [role.name for role in queried_user.roles]
    assert "ADMIN" in role_names
    assert "OFFICIAL" in role_names


def test_competency_framework_and_levels(db_session: Session):
    # 1. Create Framework
    framework = CompetencyFramework(
        name="STATISTICAL",
        description="Statistical calculations"
    )
    db_session.add(framework)
    db_session.commit()

    # 2. Create Competency
    comp = Competency(
        framework_id=framework.id,
        name="Sampling Design",
        code="STAT_SAMPLING",
        description="Design and execute sampling plans"
    )
    db_session.add(comp)
    db_session.commit()

    # 3. Create Level
    level = CompetencyLevel(
        competency_id=comp.id,
        level=3,
        name="Advanced (Analysis)",
        description="Can design sampling plans independently.",
        behavior_indicators=["Calculate weights", "Review sample sizes"]
    )
    db_session.add(level)
    db_session.commit()

    assert comp.levels[0].level == 3
    assert comp.levels[0].behavior_indicators[0] == "Calculate weights"


def test_pgvector_embedding_insertion(db_session: Session):
    # 1. Create Document
    doc = Document(
        title="Sample Survey Manual 2026",
        filename="survey_manual.pdf",
        file_type="PDF",
        file_path="/documents/survey_manual.pdf",
        file_size_bytes=1024
    )
    db_session.add(doc)
    db_session.commit()

    # 2. Create Chunk
    chunk = DocumentChunk(
        document_id=doc.id,
        chunk_index=1,
        text_content="This section explains sampling methodology for official household surveys.",
        start_char=0,
        end_char=68,
        page_number=12
    )
    db_session.add(chunk)
    db_session.commit()

    # 3. Create Vector Embedding (1536 dimensions)
    mock_vector = [0.1] * 1536
    embedding = DocumentEmbedding(
        chunk_id=chunk.id,
        model_name="text-embedding-3-small",
        embedding=mock_vector
    )
    db_session.add(embedding)
    db_session.commit()

    # Query back and verify Vector
    queried_emb = db_session.query(DocumentEmbedding).filter_by(chunk_id=chunk.id).first()
    assert queried_emb is not None
    assert len(queried_emb.embedding) == 1536
    assert queried_emb.embedding[0] == 0.1
