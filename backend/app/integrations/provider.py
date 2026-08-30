import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings
from app.schemas.provider import IGOTCourseDetail, NSSTATrainingDetail

class IGOTProvider(ABC):
    """Abstract base interface for iGOT Karmayogi course provider."""
    
    @abstractmethod
    def get_courses(self) -> List[IGOTCourseDetail]:
        """Fetch all courses available from the iGOT platform."""
        pass
        
    @abstractmethod
    def get_course_by_code(self, code: str) -> Optional[IGOTCourseDetail]:
        """Fetch a specific course details by its unique identifier code."""
        pass


class NSSTAProvider(ABC):
    """Abstract base interface for NSSTA training program provider."""
    
    @abstractmethod
    def get_training_programs(self) -> List[NSSTATrainingDetail]:
        """Fetch all training programs available from the NSSTA academy."""
        pass
        
    @abstractmethod
    def get_program_by_code(self, code: str) -> Optional[NSSTATrainingDetail]:
        """Fetch a specific training program details by its unique identifier code."""
        pass


class MockIGOTProvider(IGOTProvider):
    """Concrete implementation of IGOTProvider retrieving from synthetic JSON dataset."""
    
    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            file_path = os.path.join(settings.MOCK_DATA_DIR, "igot_courses.json")
        self.file_path = file_path
        self._load_data()
        
    def _load_data(self) -> None:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Synthetic iGOT dataset not found at: {self.file_path}")
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.courses = [IGOTCourseDetail(**c) for c in data.get("courses", [])]
        
    def get_courses(self) -> List[IGOTCourseDetail]:
        return self.courses
        
    def get_course_by_code(self, code: str) -> Optional[IGOTCourseDetail]:
        for course in self.courses:
            if course.code == code:
                return course
        return None


class MockNSSTAProvider(NSSTAProvider):
    """Concrete implementation of NSSTAProvider retrieving from synthetic JSON dataset."""
    
    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            file_path = os.path.join(settings.MOCK_DATA_DIR, "nssta_programs.json")
        self.file_path = file_path
        self._load_data()
        
    def _load_data(self) -> None:
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Synthetic NSSTA dataset not found at: {self.file_path}")
            
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.programs = [NSSTATrainingDetail(**p) for p in data.get("programs", [])]
        
    def get_training_programs(self) -> List[NSSTATrainingDetail]:
        return self.programs
        
    def get_program_by_code(self, code: str) -> Optional[NSSTATrainingDetail]:
        for program in self.programs:
            if program.code == code:
                return program
        return None
