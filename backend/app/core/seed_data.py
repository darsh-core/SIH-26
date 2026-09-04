import os
import sys
import uuid
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import Organization, RBACRole
from app.models.competency import CompetencyFramework, Competency, CompetencyLevel, JobRole, RoleCompetency

# Standard level definitions mapping level (1-5) to general description and sample indicators
LEVELS_TEMPLATE = {
    1: {
        "name": "Basic (Awareness)",
        "description": "Demonstrates basic awareness and understanding of the competency. Performs simple, routine tasks under close supervision.",
        "indicators": [
            "Defines standard terms and concepts related to the competency.",
            "Follows standard operating procedures and guidelines.",
            "Requires active supervision and guidance for non-routine tasks."
        ]
    },
    2: {
        "name": "Intermediate (Application)",
        "description": "Able to apply the competency to complete routine tasks independently. Understands and troubleshoots standard issues.",
        "indicators": [
            "Applies methods independently to typical problems.",
            "Identifies and resolves common operational issues.",
            "Needs minimal supervision on day-to-day operations."
        ]
    },
    3: {
        "name": "Advanced (Analysis)",
        "description": "Demonstrates deep understanding. Able to design, analyze, and manage complex tasks and projects.",
        "indicators": [
            "Analyzes results and optimizes processes for efficiency.",
            "Designs plans, workflows, or routines within the competency domain.",
            "Provides mentoring or operational guidance to junior colleagues."
        ]
    },
    4: {
        "name": "Expert (Evaluation)",
        "description": "Critically reviews, evaluates, and optimizes methodologies. Advises senior leadership and develops standards.",
        "indicators": [
            "Evaluates competing methodologies and selects the best fit.",
            "Formulates organizational standards, protocols, and policies.",
            "Serves as the primary point of contact for complex troubleshooting."
        ]
    },
    5: {
        "name": "Master (Synthesis/Strategy)",
        "description": "Innovates new methodologies and represents the organization at national/international forums. Shapes national policy.",
        "indicators": [
            "Synthesizes and invents novel approaches to solve systemic problems.",
            "Influences national statistical and governance frameworks.",
            "Represents the department or nation in international standard-setting bodies."
        ]
    }
}

COMPETENCY_DOMAINS = {
    "STATISTICAL": {
        "description": "Core competency domain covering statistical standards, design, collection, and analysis for official statistics.",
        "skills": [
            {"name": "Survey Design", "code": "STAT_SURVEY_DESIGN", "desc": "Designing official surveys, questionnaires, and collection tools."},
            {"name": "Sampling Methodology", "code": "STAT_SAMPLING", "desc": "Designing and executing sampling plans, calculating weights, and sample sizes."},
            {"name": "National Accounts", "code": "STAT_NAT_ACCOUNTS", "desc": "Compiling Gross Domestic Product (GDP), Gross Value Added (GVA), and national balance sheets."},
            {"name": "Price Statistics", "code": "STAT_PRICES", "desc": "Compiling Consumer Price Index (CPI), Wholesale Price Index (WPI), and inflation metrics."},
            {"name": "Labour Statistics", "code": "STAT_LABOUR", "desc": "Measuring employment, unemployment, labour force participation, and informal sector work."},
            {"name": "Agricultural Statistics", "code": "STAT_AGRICULTURE", "desc": "Estimating crop yields, land usage, forestry, and fisheries statistics."},
            {"name": "Industrial Statistics", "code": "STAT_INDUSTRY", "desc": "Compiling Index of Industrial Production (IIP) and conducting Annual Survey of Industries (ASI)."},
            {"name": "SDG Indicators", "code": "STAT_SDG", "desc": "Monitoring and reporting on UN Sustainable Development Goals indicators in the national framework."},
            {"name": "Metadata Standards", "code": "STAT_METADATA", "desc": "Documenting data according to SDMX, DDI, and other international standards."},
            {"name": "Data Quality", "code": "STAT_QUALITY", "desc": "Assessing and auditing data quality using standard statistical quality frameworks."}
        ]
    },
    "TECHNICAL": {
        "description": "Technical and computational skills required to execute data engineering, analysis, modeling, and system integrations.",
        "skills": [
            {"name": "Python", "code": "TECH_PYTHON", "desc": "Programming in Python for data processing, analysis, and automation."},
            {"name": "R", "code": "TECH_R", "desc": "Programming in R for advanced statistical computation and graphics."},
            {"name": "SQL", "code": "TECH_SQL", "desc": "Querying, designing, and optimizing relational databases."},
            {"name": "GIS", "code": "TECH_GIS", "desc": "Geospatial data analysis, mapping, and utilizing GIS tools like QGIS or ArcGIS."},
            {"name": "Data Visualization", "code": "TECH_VISUALIZATION", "desc": "Creating clear, interactive, and impactful dashboards and visual reports (e.g., Superset, Tableau)."},
            {"name": "AI/ML", "code": "TECH_AI_ML", "desc": "Implementing machine learning models and AI applications for predictive analytics."},
            {"name": "Cloud Computing", "code": "TECH_CLOUD", "desc": "Deploying, scaling, and managing infrastructure on cloud platforms (e.g., AWS, GCP, NIC Cloud)."},
            {"name": "API Integration", "code": "TECH_API", "desc": "Designing, building, and integrating RESTful and GraphQL web services."}
        ]
    },
    "DIGITAL GOVERNANCE": {
        "description": "Governance frameworks, security protocols, digital infrastructure, and privacy rules for public sector applications.",
        "skills": [
            {"name": "Cybersecurity", "code": "GOV_CYBERSECURITY", "desc": "Securing digital assets, networks, and applications against threats."},
            {"name": "Data Privacy", "code": "GOV_PRIVACY", "desc": "Understanding data protection acts, consent architectures, and anonymization methods."},
            {"name": "Digital Public Infrastructure", "code": "GOV_DPI", "desc": "Utilizing and integrating national DPIs (e.g., Aadhaar, UPI, DigiLocker, NDG)."},
            {"name": "Open Data", "code": "GOV_OPEN_DATA", "desc": "Publishing, managing, and utilizing open datasets on data.gov.in."}
        ]
    },
    "BEHAVIOURAL": {
        "description": "Soft skills and workplace competencies necessary for effective execution, collaboration, and management.",
        "skills": [
            {"name": "Leadership", "code": "BEH_LEADERSHIP", "desc": "Motivating teams, setting vision, and driving strategic projects."},
            {"name": "Communication", "code": "BEH_COMMUNICATION", "desc": "Expressing ideas clearly, drafting reports, and presenting data to stakeholders."},
            {"name": "Project Management", "code": "BEH_PROJ_MGMT", "desc": "Planning, executing, monitoring, and closing projects using standard frameworks (Agile, PMBOK)."},
            {"name": "Ethics", "code": "BEH_ETHICS", "desc": "Maintaining integrity, impartiality, and statistical confidentiality (under Collection of Statistics Act)."},
            {"name": "Decision Making", "code": "BEH_DECISION", "desc": "Analysing complex options, assessing risks, and making timely, evidence-based choices."},
            {"name": "Change Management", "code": "BEH_CHANGE_MGMT", "desc": "Guiding teams and organizations through process, technological, and cultural transformations."}
        ]
    }
}

JOB_ROLES_DATA = [
    {
        "name": "Statistical Officer",
        "code": "ROLE_STAT_OFFICER",
        "description": "Responsible for designing statistical inquiries, supervising field collection, compiling reports, and ensuring data quality.",
        "department": "National Sample Survey Office (NSSO)",
        "competencies": [
            {"code": "STAT_SURVEY_DESIGN", "level": 3, "weight": 0.8, "mandatory": True},
            {"code": "STAT_SAMPLING", "level": 3, "weight": 0.8, "mandatory": True},
            {"code": "STAT_QUALITY", "level": 3, "weight": 0.7, "mandatory": True},
            {"code": "STAT_METADATA", "level": 2, "weight": 0.6, "mandatory": False},
            {"code": "TECH_SQL", "level": 2, "weight": 0.5, "mandatory": False},
            {"code": "BEH_COMMUNICATION", "level": 3, "weight": 0.6, "mandatory": True},
            {"code": "BEH_ETHICS", "level": 4, "weight": 0.9, "mandatory": True}
        ]
    },
    {
        "name": "Data Analyst",
        "code": "ROLE_DATA_ANALYST",
        "description": "Focuses on cleaning, transforming, visualizing, and analyzing statistical datasets to derive policy insights.",
        "department": "Computer Center (MoSPI)",
        "competencies": [
            {"code": "TECH_SQL", "level": 4, "weight": 0.9, "mandatory": True},
            {"code": "TECH_PYTHON", "level": 3, "weight": 0.8, "mandatory": True},
            {"code": "TECH_VISUALIZATION", "level": 4, "weight": 0.9, "mandatory": True},
            {"code": "STAT_QUALITY", "level": 3, "weight": 0.7, "mandatory": True},
            {"code": "TECH_R", "level": 2, "weight": 0.5, "mandatory": False},
            {"code": "BEH_DECISION", "level": 2, "weight": 0.5, "mandatory": False},
            {"code": "BEH_ETHICS", "level": 4, "weight": 0.9, "mandatory": True}
        ]
    },
    {
        "name": "Survey Methodologist",
        "code": "ROLE_SURVEY_METHODOLOGIST",
        "description": "High-level designer of complex survey frames, sampling methodologies, and estimation frameworks for national censuses and large scale surveys.",
        "department": "Survey Design and Research Division (SDRD)",
        "competencies": [
            {"code": "STAT_SURVEY_DESIGN", "level": 5, "weight": 1.0, "mandatory": True},
            {"code": "STAT_SAMPLING", "level": 5, "weight": 1.0, "mandatory": True},
            {"code": "STAT_QUALITY", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "STAT_METADATA", "level": 3, "weight": 0.7, "mandatory": True},
            {"code": "TECH_R", "level": 3, "weight": 0.6, "mandatory": False},
            {"code": "BEH_COMMUNICATION", "level": 3, "weight": 0.6, "mandatory": False},
            {"code": "BEH_ETHICS", "level": 5, "weight": 1.0, "mandatory": True}
        ]
    },
    {
        "name": "Statistical Data Engineer",
        "code": "ROLE_DATA_ENGINEER",
        "description": "Architects data pipelines, databases, and api integrations to aggregate data from multiple administrative and survey sources.",
        "department": "National Data Warehouse (NDW)",
        "competencies": [
            {"code": "TECH_SQL", "level": 5, "weight": 1.0, "mandatory": True},
            {"code": "TECH_PYTHON", "level": 4, "weight": 0.9, "mandatory": True},
            {"code": "TECH_API", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "TECH_CLOUD", "level": 3, "weight": 0.7, "mandatory": True},
            {"code": "GOV_CYBERSECURITY", "level": 3, "weight": 0.6, "mandatory": True},
            {"code": "GOV_PRIVACY", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "BEH_ETHICS", "level": 4, "weight": 0.9, "mandatory": True}
        ]
    },
    {
        "name": "Statistical Supervisor",
        "code": "ROLE_STAT_SUPERVISOR",
        "description": "Supervises data collection exercises, field surveys, and compiles and validates aggregate reports.",
        "department": "Field Operations Division (FOD)",
        "competencies": [
            {"code": "STAT_SURVEY_DESIGN", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "STAT_QUALITY", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "BEH_LEADERSHIP", "level": 3, "weight": 0.8, "mandatory": True},
            {"code": "BEH_PROJ_MGMT", "level": 3, "weight": 0.7, "mandatory": True},
            {"code": "BEH_COMMUNICATION", "level": 3, "weight": 0.7, "mandatory": True},
            {"code": "BEH_ETHICS", "level": 4, "weight": 0.9, "mandatory": True}
        ]
    },
    {
        "name": "Official Statistics Manager",
        "code": "ROLE_STAT_MANAGER",
        "description": "Manages high-profile statistical divisions, coordinates reports like National Accounts, price indices, and handles planning and policy analysis.",
        "department": "Central Statistics Office (CSO)",
        "competencies": [
            {"code": "STAT_NAT_ACCOUNTS", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "BEH_LEADERSHIP", "level": 4, "weight": 0.9, "mandatory": True},
            {"code": "BEH_DECISION", "level": 4, "weight": 0.9, "mandatory": True},
            {"code": "BEH_CHANGE_MGMT", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "BEH_PROJ_MGMT", "level": 4, "weight": 0.8, "mandatory": True},
            {"code": "BEH_ETHICS", "level": 5, "weight": 1.0, "mandatory": True}
        ]
    }
]

def seed_database(db: Session):
    print("Starting database seeding...")

    # 1. Seed default organization (MoSPI)
    mospi = db.query(Organization).filter_by(code="MoSPI").first()
    if not mospi:
        mospi = Organization(
            name="Ministry of Statistics and Programme Implementation",
            code="MoSPI",
            description="The apex body in the official statistical system of India.",
            metadata_json={"country": "India", "headquarters": "New Delhi"}
        )
        db.add(mospi)
        db.flush()
        print(f"Seeded Organization: {mospi.name}")
    else:
        print("Organization 'MoSPI' already exists.")

    # 2. Seed RBAC Roles
    roles = ["ADMIN", "OFFICIAL", "SUPERVISOR", "MANAGER", "TRAINER", "EVALUATOR"]
    role_entities = {}
    for rname in roles:
        role = db.query(RBACRole).filter_by(name=rname).first()
        if not role:
            role = RBACRole(
                name=rname,
                description=f"System role representing a {rname.lower()} user."
            )
            db.add(role)
            db.flush()
            print(f"Seeded RBAC Role: {rname}")
        role_entities[rname] = role

    # 3. Seed Competency Framework and Competencies
    comp_map = {} # Maps code -> Competency object
    for fname, fdata in COMPETENCY_DOMAINS.items():
        framework = db.query(CompetencyFramework).filter_by(name=fname).first()
        if not framework:
            framework = CompetencyFramework(
                name=fname,
                description=fdata["description"]
            )
            db.add(framework)
            db.flush()
            print(f"Seeded Framework: {fname}")
        
        for cdata in fdata["skills"]:
            comp = db.query(Competency).filter_by(code=cdata["code"]).first()
            if not comp:
                comp = Competency(
                    framework_id=framework.id,
                    name=cdata["name"],
                    code=cdata["code"],
                    description=cdata["desc"]
                )
                db.add(comp)
                db.flush()
                print(f"  Seeded Competency: {cdata['name']} ({cdata['code']})")
                
                # Create Level 1-5 definitions
                for lvl, templ in LEVELS_TEMPLATE.items():
                    clevel = CompetencyLevel(
                        competency_id=comp.id,
                        level=lvl,
                        name=templ["name"],
                        description=templ["description"],
                        behavior_indicators=templ["indicators"]
                    )
                    db.add(clevel)
                db.flush()
            comp_map[cdata["code"]] = comp

    # 4. Seed Job Roles and Role Competency mappings
    for jr in JOB_ROLES_DATA:
        job_role = db.query(JobRole).filter_by(code=jr["code"]).first()
        if not job_role:
            job_role = JobRole(
                name=jr["name"],
                code=jr["code"],
                description=jr["description"],
                department=jr["department"]
            )
            db.add(job_role)
            db.flush()
            print(f"Seeded Job Role: {jr['name']}")

            # Seed role-specific competencies
            for rcomp in jr["competencies"]:
                comp = comp_map.get(rcomp["code"])
                if comp:
                    role_comp = RoleCompetency(
                        job_role_id=job_role.id,
                        competency_id=comp.id,
                        required_level=rcomp["level"],
                        weight=rcomp["weight"],
                        is_mandatory=rcomp["mandatory"]
                    )
                    db.add(role_comp)
            db.flush()
        else:
            print(f"Job Role '{jr['name']}' already exists.")

    # 4.5 Seed Providers, Courses, and Training Programs (Candidate Catalogue)
    from app.models.course import Provider, Course, CourseCompetency, TrainingProgram, TrainingCompetency, CourseModule, CourseLesson
    from app.integrations.provider import MockIGOTProvider, MockNSSTAProvider

    # Add iGOT Provider
    igot_provider_name = "iGOT Karmayogi"
    db_igot_prov = db.query(Provider).filter_by(name=igot_provider_name).first()
    if not db_igot_prov:
        db_igot_prov = Provider(
            name=igot_provider_name,
            description="iGOT Karmayogi official capability building platform",
            url="https://igot-demo.gov.in",
            status="ACTIVE"
        )
        db.add(db_igot_prov)
        db.flush()
        print(f"Seeded Provider: {igot_provider_name}")

    # Add NSSTA Provider
    nssta_provider_name = "National Statistical Systems Training Academy (NSSTA)"
    db_nssta_prov = db.query(Provider).filter_by(name=nssta_provider_name).first()
    if not db_nssta_prov:
        db_nssta_prov = Provider(
            name=nssta_provider_name,
            description="NSSTA apex training institute for official statistics",
            url="https://nssta-demo.gov.in",
            status="ACTIVE"
        )
        db.add(db_nssta_prov)
        db.flush()
        print(f"Seeded Provider: {nssta_provider_name}")

    # Seed iGOT Courses
    igot = MockIGOTProvider()
    courses = igot.get_courses()
    for c in courses:
        db_course = db.query(Course).filter_by(code=c.code).first()
        if not db_course:
            db_course = Course(
                provider_id=db_igot_prov.id,
                code=c.code,
                title=c.title,
                description=c.description,
                duration_minutes=c.duration_minutes,
                difficulty=c.difficulty,
                language=c.language,
                url=c.url,
                metadata_json={}
            )
            db.add(db_course)
            db.flush()
            print(f"  Seeded Course: {c.title}")
            
            for mapping in c.competency_mappings:
                comp = comp_map.get(mapping.competency_code)
                if comp:
                    cc = CourseCompetency(
                        course_id=db_course.id,
                        competency_id=comp.id,
                        target_level=mapping.target_level,
                        weight=mapping.weight
                    )
                    db.add(cc)
            db.flush()

    # Seed NSSTA Programs
    nssta = MockNSSTAProvider()
    programs = nssta.get_training_programs()
    for p in programs:
        db_prog = db.query(TrainingProgram).filter_by(code=p.code).first()
        if not db_prog:
            db_prog = TrainingProgram(
                provider_id=db_nssta_prov.id,
                code=p.code,
                title=p.title,
                description=p.description,
                duration_days=p.duration_days,
                location=p.location,
                mode=p.mode,
                eligibility_criteria=p.eligibility_criteria,
                tpac_recommendation=p.tpac_recommendation,
                metadata_json={}
            )
            db.add(db_prog)
            db.flush()
            print(f"  Seeded Training Program: {p.title}")
            
            for mapping in p.competency_mappings:
                comp = comp_map.get(mapping.competency_code)
                if comp:
                    tc = TrainingCompetency(
                        training_program_id=db_prog.id,
                        competency_id=comp.id,
                        target_level=mapping.target_level,
                        weight=mapping.weight
                    )
                    db.add(tc)
            db.flush()

    # 5. Seed Demo User
    # Credentials: employee@mospi.gov.in / password123
    from app.core.security import get_password_hash
    from app.models.user import AppUser, UserProfile
    from app.models.competency import UserCompetency
    
    demo_email = "employee@mospi.gov.in"
    demo_user = db.query(AppUser).filter_by(email=demo_email).first()
    if not demo_user:
        # Get MoSPI organization
        mospi_org = db.query(Organization).filter_by(code="MoSPI").first()
        # Get Job Role
        stat_officer_role = db.query(JobRole).filter_by(code="ROLE_STAT_OFFICER").first()
        
        # Create AppUser
        demo_user = AppUser(
            email=demo_email,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False,
            organization_id=mospi_org.id if mospi_org else None
        )
        db.add(demo_user)
        db.flush()
        
        # Map RBAC role OFFICIAL
        official_role = db.query(RBACRole).filter_by(name="OFFICIAL").first()
        if official_role:
            demo_user.roles.append(official_role)
            
        # Create UserProfile for Arun Kumar (Statistical Officer - Agricultural Statistics)
        demo_profile = UserProfile(
            user_id=demo_user.id,
            first_name="Arun",
            last_name="Kumar",
            designation="Statistical Officer",
            department="Agricultural Statistics Division",
            contact_number="9876543210",
            gender="Male",
            date_of_joining=datetime.strptime("2024-01-15", "%Y-%m-%d").date(),
            bio="Statistical Officer specializing in Agricultural Statistics and Sample Surveys.",
            job_role_id=stat_officer_role.id if stat_officer_role else None
        )
        db.add(demo_profile)
        # Current competency levels
        current_levels = {
            "STAT_SURVEY_DESIGN": 3.7,
            "STAT_SAMPLING": 2.3,
            "STAT_QUALITY": 3.4,
            "TECH_PYTHON": 1.8,
            "TECH_SQL": 3.1,
            "STAT_METADATA": 2.1
        }
        
        for code, level in current_levels.items():
            comp = comp_map.get(code)
            if comp:
                uc = UserCompetency(
                    user_id=demo_user.id,
                    competency_id=comp.id,
                    current_level=level,
                    last_evaluated_at=datetime.utcnow(),
                    status="EVALUATED"
                )
                db.add(uc)
        print("Seeded Demo User: Arun Kumar (employee@mospi.gov.in)")
        db.flush()

    # 5b. Seed Trainer User
    # Credentials: trainer@mospi.gov.in / password123
    trainer_email = "trainer@mospi.gov.in"
    trainer_user = db.query(AppUser).filter_by(email=trainer_email).first()
    if not trainer_user:
        mospi_org = db.query(Organization).filter_by(code="MoSPI").first()
        trainer_user = AppUser(
            email=trainer_email,
            hashed_password=get_password_hash("password123"),
            is_active=True,
            is_superuser=False,
            organization_id=mospi_org.id if mospi_org else None
        )
        db.add(trainer_user)
        db.flush()
        
        trainer_role = db.query(RBACRole).filter_by(name="TRAINER").first()
        if trainer_role:
            trainer_user.roles.append(trainer_role)
            
        trainer_profile = UserProfile(
            user_id=trainer_user.id,
            first_name="Dr. Sunita",
            last_name="Sharma",
            designation="Senior Training Director",
            department="National Statistical Systems Training Academy (NSSTA)",
            contact_number="9876543211",
            gender="Female",
            date_of_joining=datetime.strptime("2020-05-10", "%Y-%m-%d").date(),
            bio="Senior Faculty & Assessment Reviewer at NSSTA Greater Noida."
        )
        db.add(trainer_profile)
        db.flush()
        print("Seeded Trainer User: Dr. Sunita Sharma (trainer@mospi.gov.in)")

    # 6. Seed an Assessment
    from app.models.assessment import Assessment, Question, QuestionOption, QuestionCompetency
    existing_assess = db.query(Assessment).filter_by(title="Sampling Methodology Core Assessment").first()
    if not existing_assess:
        sampling_comp = comp_map.get("STAT_SAMPLING")
        # Create Assessment
        existing_assess = Assessment(
            title="Sampling Methodology Core Assessment",
            description="Assessment to evaluate Sampling Methodology and Survey Design competencies.",
            time_limit_minutes=30,
            pass_percentage=60.0,
            is_ai_generated=False
        )
        db.add(existing_assess)
        db.flush()
        
        # Add Questions
        # Q1: Probability Sampling
        q1 = Question(
            assessment_id=existing_assess.id,
            text="Which sampling design gives every member of the population an equal and known chance of being selected?",
            question_type="MCQ",
            difficulty="Medium",
            explanation="Simple Random Sampling is a probability sampling method where all subsets of the frame have an equal probability of selection.",
            confidence=1.0
        )
        db.add(q1)
        db.flush()
        
        o1 = QuestionOption(question_id=q1.id, text="Simple Random Sampling", is_correct=True)
        o2 = QuestionOption(question_id=q1.id, text="Quota Sampling", is_correct=False)
        o3 = QuestionOption(question_id=q1.id, text="Snowball Sampling", is_correct=False)
        o4 = QuestionOption(question_id=q1.id, text="Convenience Sampling", is_correct=False)
        db.add_all([o1, o2, o3, o4])
        
        # Link Q1 to STAT_SAMPLING level 3
        qc1 = QuestionCompetency(question_id=q1.id, competency_id=sampling_comp.id, target_level=3, weight=1.0)
        db.add(qc1)
        
        # Q2: Stratified Sampling
        q2 = Question(
            assessment_id=existing_assess.id,
            text="What is the primary purpose of stratification in sampling design?",
            question_type="MCQ",
            difficulty="Medium",
            explanation="Stratification ensures that sub-populations (strata) are adequately represented and reduces sampling variance.",
            confidence=1.0
        )
        db.add(q2)
        db.flush()
        
        o2_1 = QuestionOption(question_id=q2.id, text="To increase sampling variance", is_correct=False)
        o2_2 = QuestionOption(question_id=q2.id, text="To ensure sub-populations are represented and reduce overall variance", is_correct=True)
        o2_3 = QuestionOption(question_id=q2.id, text="To make fieldwork easier", is_correct=False)
        o2_4 = QuestionOption(question_id=q2.id, text="To eliminate nonsampling errors", is_correct=False)
        db.add_all([o2_1, o2_2, o2_3, o2_4])
        
        qc2 = QuestionCompetency(question_id=q2.id, competency_id=sampling_comp.id, target_level=3, weight=1.0)
        db.add(qc2)
        
        print("Seeded Demo Assessment: Sampling Methodology Core Assessment")
        db.flush()

    # 7. Seed Course Modules & Lessons for Demo iGOT Player
    seed_course_modules_and_lessons(db)

    db.commit()
    print("Database seeding completed successfully!")


def seed_course_modules_and_lessons(db):
    from app.models.course import Course, CourseModule, CourseLesson

    TAILORED_MODULES = {
        "IGOT_COMP_STATS_01": [
            {
                "code": "MOD_01",
                "title": "Principles of Official Survey Design",
                "description": "Understanding survey objectives, target population, and sample frame development for official surveys.",
                "duration": 45,
                "lessons": [
                    {
                        "title": "Defining Survey Scope & Objectives",
                        "content": "Official government surveys require rigorous alignment with policy objectives. Under MoSPI frameworks, survey objectives must establish clear operational definitions, target populations, and primary inquiry domains before questionnaire formulation. Field teams must distinguish between target populations and study populations to avoid undercoverage bias.",
                        "duration": 20
                    },
                    {
                        "title": "Sampling Frame Construction & Validation",
                        "content": "A robust sampling frame is the cornerstone of survey validity. In India, urban sampling frames typically leverage the Urban Frame Survey (UFS) blocks maintained by the Field Operations Division (FOD), while rural frames utilize the latest Census Village directories. Frames must undergo periodic auxiliary auditing to identify boundary changes, de-notified settlements, or newly urbanized agglomerations.",
                        "duration": 25
                    }
                ]
            },
            {
                "code": "MOD_02",
                "title": "Questionnaire Design & Field Pre-testing",
                "description": "Structuring schedules, skip-patterns, field validation rules, and conducting pilot tests.",
                "duration": 60,
                "lessons": [
                    {
                        "title": "Structured Schedules & Response Standardization",
                        "content": "Questionnaire schedules in MoSPI surveys require standardized code lists (e.g. NIC-2008 for economic activities, NCO-2015 for occupations). Standardized terminology prevents enumerator misclassification and facilitates inter-temporal comparability across survey rounds.",
                        "duration": 30
                    },
                    {
                        "title": "Pilot Testing & Cognitive Interviewing",
                        "content": "Pilot testing ensures respondents interpret questions as intended. Cognitive interviews test respondent comprehension, recall strategy, judgment, and response editing, isolating ambiguous phrases before nationwide deployment.",
                        "duration": 30
                    }
                ]
            },
            {
                "code": "MOD_03",
                "title": "Fieldwork Execution & Non-sampling Error Control",
                "description": "Field supervision, verification protocols, call-back procedures, and managing non-response.",
                "duration": 75,
                "lessons": [
                    {
                        "title": "Supervisory Inspection & Concurrent Verification",
                        "content": "High-quality survey execution depends on multi-tier supervision. Senior Statistical Officers conduct concurrent inspections of interviews and independent re-interviews on a stratified subsample of households to measure and minimize enumerator variance.",
                        "duration": 35
                    },
                    {
                        "title": "Non-Response Imputation & Treatment",
                        "content": "When households are unavailable or refuse cooperation, strict call-back schedules (minimum 3 attempts) are mandatory. Residual non-response is handled using weighting adjustments (cell-mean or hot-deck imputation) to preserve population estimate integrity.",
                        "duration": 40
                    }
                ]
            }
        ],
        "IGOT_COMP_STATS_03": [
            {
                "code": "MOD_01",
                "title": "Probability Sampling Fundamentals",
                "description": "Simple random sampling, systematic selection, and probability proportional to size (PPS).",
                "duration": 50,
                "lessons": [
                    {
                        "title": "Basic Sampling Principles in Official Statistics",
                        "content": "In official inquiries, every sampling unit must have a known, non-zero probability of selection. Simple Random Sampling Without Replacement (SRSWOR) provides the benchmark design with unbiased estimator properties: E(y_bar) = Y_bar.",
                        "duration": 25
                    },
                    {
                        "title": "Probability Proportional to Size (PPS) Selection",
                        "content": "When Primary Sampling Units (PSUs) such as villages or UFS blocks vary greatly in population, PPS sampling (e.g. Hansen-Hurwitz or Horvitz-Thompson estimation) improves estimation efficiency by granting larger clusters proportional inclusion probability.",
                        "duration": 25
                    }
                ]
            },
            {
                "code": "MOD_02",
                "title": "Stratified Multi-Stage Sampling in NSSO Surveys",
                "description": "Stratification strategies, multi-stage cluster sampling, and ultimate stage unit (USU) selection.",
                "duration": 70,
                "lessons": [
                    {
                        "title": "Stratification Criteria & Variance Reduction",
                        "content": "Stratification groups heterogeneous populations into homogeneous strata (e.g. dividing districts into rural agricultural zones vs non-agricultural belts). Variance within strata is minimized, substantially lowering total survey error.",
                        "duration": 35
                    },
                    {
                        "title": "Multi-Stage Sampling & Sub-sampling in the Field",
                        "content": "In nationwide NSS surveys, multi-stage design is standard: 1st Stage Units (FSUs) are villages/blocks, and 2nd Stage Units (SSUs) are households. This balance minimizes travel overhead while achieving national representativeness.",
                        "duration": 35
                    }
                ]
            },
            {
                "code": "MOD_03",
                "title": "Estimation Procedures & Multiplier Generation",
                "description": "Deriving sampling weights, design multipliers, and calculating margins of error.",
                "duration": 60,
                "lessons": [
                    {
                        "title": "Inverse Probability Weighting (Multipliers)",
                        "content": "Survey estimates aggregate sample observations via multipliers equal to the inverse inclusion probability: w_i = 1 / pi_i. Multipliers are further calibrated using post-stratification benchmarked against national demographic projections.",
                        "duration": 30
                    },
                    {
                        "title": "Standard Error & Confidence Intervals",
                        "content": "Official statistics reports must publish Relative Standard Error (RSE) alongside point estimates. Estimates with RSE > 20% are flagged with cautionary reliability caveats.",
                        "duration": 30
                    }
                ]
            }
        ],
        "IGOT_COMP_STATS_05": [
            {
                "code": "MOD_01",
                "title": "National Quality Assurance Framework (NQAF)",
                "description": "UN-NQAF and MoSPI statistical audit guidelines.",
                "duration": 60,
                "lessons": [
                    {
                        "title": "The Six Dimensions of Statistical Quality",
                        "content": "Official statistical outputs must adhere to: Relevance, Accuracy, Timeliness, Accessibility, Comparability, and Coherence. Balancing timeliness with accuracy is a core operational challenge in release schedules.",
                        "duration": 30
                    },
                    {
                        "title": "Auditing Institutional Quality Commitments",
                        "content": "Data producers must maintain transparency in methodology, publish revision policies, and implement statistical disclosure controls before microdata release.",
                        "duration": 30
                    }
                ]
            },
            {
                "code": "MOD_02",
                "title": "Data Validation, Consistency Rules & Audits",
                "description": "Computer-assisted personal interviewing (CAPI) validation and post-enumeration audits.",
                "duration": 60,
                "lessons": [
                    {
                        "title": "Automated Validation Rules in CAPI Systems",
                        "content": "Modern CAPI tablets enforce hard and soft consistency checks at the point of entry (e.g., respondent age vs child age, reported acreage vs crop yield limits), preventing logical contradictions before data leaves the field.",
                        "duration": 30
                    },
                    {
                        "title": "Outlier Detection and Statistical Imputation",
                        "content": "Statistical outlier screening utilizes Mahalanobis distance, Tukey's fences, and IQR distributions to flag spurious survey entries requiring supervisory re-verification.",
                        "duration": 30
                    }
                ]
            }
        ],
        "IGOT_COMP_TECH_01": [
            {
                "code": "MOD_01",
                "title": "Python & Pandas for Official Statistical Microdata",
                "description": "Loading, cleaning, and preparing large-scale survey datasets.",
                "duration": 60,
                "lessons": [
                    {
                        "title": "Importing Fixed-Width & CSV Survey Files",
                        "content": "NSS microdata is distributed in fixed-width or structured CSV formats. Using pandas.read_fwf() and read_csv() with optimized categorical dtypes enables fast parsing of millions of records.",
                        "duration": 30
                    },
                    {
                        "title": "Handling Missing Data & Coding Systems",
                        "content": "Converting MoSPI convention codes (e.g. 99 for not reported, -1 for missing) into proper NaN values and creating verified analytical subsets.",
                        "duration": 30
                    }
                ]
            },
            {
                "code": "MOD_02",
                "title": "Survey Weighting & Aggregate Estimations in Python",
                "description": "Applying multipliers to generate national totals and sub-group tables.",
                "duration": 60,
                "lessons": [
                    {
                        "title": "Weighted Means and Total Estimation",
                        "content": "Calculating unweighted vs weighted statistics using numpy.average(data['income'], weights=data['multiplier']) to compute official population estimates.",
                        "duration": 30
                    },
                    {
                        "title": "Cross-tabulation & Disaggregation",
                        "content": "Generating disaggregated state-level and sector-level statistical tables with confidence intervals using groupby and aggregation pipelines.",
                        "duration": 30
                    }
                ]
            }
        ]
    }

    courses = db.query(Course).all()
    for course in courses:
        existing_mods = db.query(CourseModule).filter_by(course_id=course.id).count()
        if existing_mods > 0:
            continue

        mods_data = TAILORED_MODULES.get(course.code)
        if not mods_data:
            # Generate 3 realistic default modules
            mods_data = [
                {
                    "code": "MOD_01",
                    "title": f"Foundations of {course.title}",
                    "description": f"Core statutory context, standards, and conceptual foundations for {course.title}.",
                    "duration": 45,
                    "lessons": [
                        {
                            "title": "Introduction & National Framework",
                            "content": f"This module introduces the key principles and official guidelines governing {course.title} within India's statistical system.",
                            "duration": 20
                        },
                        {
                            "title": "Operational Guidelines & Standards",
                            "content": f"Deep dive into standard operating procedures, documentation rules, and compliance requirements for {course.title}.",
                            "duration": 25
                        }
                    ]
                },
                {
                    "code": "MOD_02",
                    "title": "Implementation Procedures & Methodologies",
                    "description": f"Practical execution techniques and field workflows for {course.title}.",
                    "duration": 60,
                    "lessons": [
                        {
                            "title": "Field Workflows & Data Collection",
                            "content": "Detailed step-by-step methodologies for data compilation, consistency checks, and error prevention.",
                            "duration": 30
                        },
                        {
                            "title": "Data Processing & Tabulation",
                            "content": "Aggregating, verifying, and generating official statistics tables according to ministerial release standards.",
                            "duration": 30
                        }
                    ]
                },
                {
                    "code": "MOD_03",
                    "title": "Quality Audits & Statistical Reporting",
                    "description": f"Auditing quality, error handling, and disseminating outputs for {course.title}.",
                    "duration": 45,
                    "lessons": [
                        {
                            "title": "Quality Metrics & Validation Checks",
                            "content": "Applying statistical checks, calculating standard errors, and preparing data validation audit reports.",
                            "duration": 20
                        },
                        {
                            "title": "Final Review & Publication Standards",
                            "content": "Compliance with national publication standards, metadata documentation, and data dissemination protocols.",
                            "duration": 25
                        }
                    ]
                }
            ]

        for m_idx, m_info in enumerate(mods_data, start=1):
            mod = CourseModule(
                course_id=course.id,
                code=m_info["code"],
                title=m_info["title"],
                description=m_info["description"],
                sequence_order=m_idx,
                duration_minutes=m_info.get("duration", 45),
                is_required=True,
                metadata_json={}
            )
            db.add(mod)
            db.flush()

            for l_idx, l_info in enumerate(m_info.get("lessons", []), start=1):
                lesson = CourseLesson(
                    module_id=mod.id,
                    title=l_info["title"],
                    content=l_info["content"],
                    duration_minutes=l_info.get("duration", 20),
                    sequence_order=l_idx,
                    metadata_json={}
                )
                db.add(lesson)

        db.flush()
        print(f"  Seeded modules & lessons for: {course.title}")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
