from models import SessionLocal, Base, engine, Role, Skill, RoleSkill, Course

Base.metadata.create_all(bind=engine)
db = SessionLocal()

def seed_data():
    if db.query(Role).first():
        print("Database already seeded.")
        return

    # Add Skills
    skills = [
        Skill(name="Statistics", category="Core"),
        Skill(name="Python", category="Technical"),
        Skill(name="SQL", category="Technical"),
        Skill(name="GIS", category="Domain"),
        Skill(name="Machine Learning", category="Advanced")
    ]
    db.add_all(skills)
    db.commit()

    # Get skill IDs
    s_stats = db.query(Skill).filter(Skill.name == "Statistics").first()
    s_python = db.query(Skill).filter(Skill.name == "Python").first()
    s_sql = db.query(Skill).filter(Skill.name == "SQL").first()
    s_gis = db.query(Skill).filter(Skill.name == "GIS").first()
    s_ml = db.query(Skill).filter(Skill.name == "Machine Learning").first()

    # Add Role
    role = Role(name="Statistical Data Analyst")
    db.add(role)
    db.commit()

    # Add RoleSkills (Required Competencies)
    role_skills = [
        RoleSkill(role_id=role.id, skill_id=s_stats.id, required_level=4, importance=1.0),
        RoleSkill(role_id=role.id, skill_id=s_python.id, required_level=4, importance=0.8),
        RoleSkill(role_id=role.id, skill_id=s_sql.id, required_level=3, importance=0.9),
        RoleSkill(role_id=role.id, skill_id=s_gis.id, required_level=3, importance=0.6),
        RoleSkill(role_id=role.id, skill_id=s_ml.id, required_level=3, importance=0.9)
    ]
    db.add_all(role_skills)
    db.commit()

    # Add Courses
    courses = [
        Course(title="Machine Learning Fundamentals", provider="iGOT Karmayogi", description="Intro to ML", url="https://igot.gov.in", target_skill_id=s_ml.id, difficulty_level=2),
        Course(title="Geospatial Data Analysis", provider="MoSPI Training", description="Learn GIS", url="https://igot.gov.in", target_skill_id=s_gis.id, difficulty_level=2),
        Course(title="Advanced SQL for Analytics", provider="NIC", description="Complex Queries", url="https://igot.gov.in", target_skill_id=s_sql.id, difficulty_level=3),
        Course(title="Python for Data Science", provider="iGOT Karmayogi", description="Pandas & NumPy", url="https://igot.gov.in", target_skill_id=s_python.id, difficulty_level=2),
        Course(title="Applied Statistics in Gov", provider="MoSPI", description="Gov Data", url="https://igot.gov.in", target_skill_id=s_stats.id, difficulty_level=3),
    ]
    db.add_all(courses)
    db.commit()
    print("Database seeded successfully with MoSPI data!")

seed_data()
