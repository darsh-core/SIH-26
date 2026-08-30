import os
import pytest
from app.core.config import settings
from app.integrations.provider import MockIGOTProvider, MockNSSTAProvider
from app.schemas.provider import IGOTCourseDetail, NSSTATrainingDetail

def test_mock_igot_provider():
    # Arrange & Act
    provider = MockIGOTProvider()
    courses = provider.get_courses()
    
    # Assert
    assert len(courses) > 0
    assert all(isinstance(c, IGOTCourseDetail) for c in courses)
    
    # Verify course data properties
    first_course = courses[0]
    assert first_course.code == "IGOT_COMP_STATS_01"
    assert first_course.title == "Introduction to Official Survey Design"
    assert first_course.duration_minutes == 180
    assert first_course.difficulty == "Beginner"
    assert first_course.language == "English"
    
    # Verify mapped competencies
    assert len(first_course.competency_mappings) == 1
    mapping = first_course.competency_mappings[0]
    assert mapping.competency_code == "STAT_SURVEY_DESIGN"
    assert mapping.target_level == 1
    assert mapping.weight == 1.0
    
    # Test lookup by code
    course_lookup = provider.get_course_by_code("IGOT_COMP_STATS_01")
    assert course_lookup is not None
    assert course_lookup.title == first_course.title
    
    # Lookup non-existent
    assert provider.get_course_by_code("INVALID_CODE") is None


def test_mock_nssta_provider():
    # Arrange & Act
    provider = MockNSSTAProvider()
    programs = provider.get_training_programs()
    
    # Assert
    assert len(programs) > 0
    assert all(isinstance(p, NSSTATrainingDetail) for p in programs)
    
    # Verify training program properties
    first_prog = programs[0]
    assert first_prog.code == "NSSTA_PROG_STATS_01"
    assert first_prog.title == "Professional Training on Sampling Design & Estimation Methods"
    assert first_prog.duration_days == 10
    assert first_prog.location == "Greater Noida, UP"
    assert first_prog.mode == "OFFLINE"
    assert "Indian Statistical Service" in first_prog.eligibility_criteria
    assert "TPAC" in first_prog.tpac_recommendation
    
    # Verify mapped competencies
    assert len(first_prog.competency_mappings) == 2
    sampling_mapping = next(m for m in first_prog.competency_mappings if m.competency_code == "STAT_SAMPLING")
    assert sampling_mapping.target_level == 3
    assert sampling_mapping.weight == 1.0
    
    # Test lookup by code
    prog_lookup = provider.get_program_by_code("NSSTA_PROG_STATS_01")
    assert prog_lookup is not None
    assert prog_lookup.title == first_prog.title
    
    # Lookup non-existent
    assert provider.get_program_by_code("INVALID_CODE") is None
