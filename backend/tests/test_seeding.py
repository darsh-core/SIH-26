from sqlalchemy.orm import Session
from app.core.seed_data import seed_database
from app.models.user import Organization, RBACRole
from app.models.competency import CompetencyFramework, Competency, CompetencyLevel, JobRole, RoleCompetency

def test_database_seeding(db_session: Session):
    # 1. Run seed script
    seed_database(db_session)
    
    # 2. Verify Organization
    org = db_session.query(Organization).filter_by(code="MoSPI").first()
    assert org is not None
    assert org.name == "Ministry of Statistics and Programme Implementation"
    
    # 3. Verify RBAC Roles
    roles = db_session.query(RBACRole).all()
    assert len(roles) == 4
    role_names = [r.name for r in roles]
    assert "ADMIN" in role_names
    assert "OFFICIAL" in role_names
    assert "SUPERVISOR" in role_names
    assert "MANAGER" in role_names
    
    # 4. Verify Competency Frameworks
    frameworks = db_session.query(CompetencyFramework).all()
    assert len(frameworks) == 4
    fw_names = [f.name for f in frameworks]
    assert "STATISTICAL" in fw_names
    assert "TECHNICAL" in fw_names
    assert "DIGITAL GOVERNANCE" in fw_names
    assert "BEHAVIOURAL" in fw_names
    
    # 5. Verify Specific Competencies and Level Count
    survey_design = db_session.query(Competency).filter_by(code="STAT_SURVEY_DESIGN").first()
    assert survey_design is not None
    assert survey_design.name == "Survey Design"
    
    # Verify Levels 1-5 exist for it
    levels = db_session.query(CompetencyLevel).filter_by(competency_id=survey_design.id).all()
    assert len(levels) == 5
    levels.sort(key=lambda x: x.level)
    assert [l.level for l in levels] == [1, 2, 3, 4, 5]
    assert levels[0].name == "Basic (Awareness)"
    assert levels[4].name == "Master (Synthesis/Strategy)"
    
    # 6. Verify Job Roles Seeding
    job_roles = db_session.query(JobRole).all()
    assert len(job_roles) == 6
    role_codes = [jr.code for jr in job_roles]
    assert "ROLE_STAT_OFFICER" in role_codes
    assert "ROLE_DATA_ANALYST" in role_codes
    assert "ROLE_SURVEY_METHODOLOGIST" in role_codes
    assert "ROLE_DATA_ENGINEER" in role_codes
    assert "ROLE_STAT_SUPERVISOR" in role_codes
    assert "ROLE_STAT_MANAGER" in role_codes
    
    # 7. Verify Role-Competency mapping details
    # Survey Methodologist should require Survey Design (STAT_SURVEY_DESIGN) level 5
    survey_methodologist = db_session.query(JobRole).filter_by(code="ROLE_SURVEY_METHODOLOGIST").first()
    assert survey_methodologist is not None
    
    mappings = db_session.query(RoleCompetency).filter_by(job_role_id=survey_methodologist.id).all()
    assert len(mappings) > 0
    
    survey_design_mapping = None
    for mapping in mappings:
        if mapping.competency.code == "STAT_SURVEY_DESIGN":
            survey_design_mapping = mapping
            break
            
    assert survey_design_mapping is not None
    assert survey_design_mapping.required_level == 5
    assert survey_design_mapping.weight == 1.0
    assert survey_design_mapping.is_mandatory is True
