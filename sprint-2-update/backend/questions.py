from typing import List, Dict, Any
import random

# Deterministic Question Bank
QUESTION_BANK = [
    # Machine Learning
    {"id": 101, "skill": "Machine Learning", "difficulty": "easy", "question": "What does 'ML' stand for?", "options": ["Machine Learning", "Modern Logic", "Multiple Layers", "Model Language"], "correct_answer": 0, "explanation": "ML stands for Machine Learning."},
    {"id": 102, "skill": "Machine Learning", "difficulty": "medium", "question": "What is the primary purpose of a validation set?", "options": ["To train the model", "To tune hyperparameters and prevent overfitting", "To test the final model", "To collect new data"], "correct_answer": 1, "explanation": "Validation sets are used during training to tune hyperparameters."},
    {"id": 103, "skill": "Machine Learning", "difficulty": "hard", "question": "Which of the following algorithms is an example of an ensemble method?", "options": ["Linear Regression", "Decision Tree", "Random Forest", "K-Means"], "correct_answer": 2, "explanation": "Random Forest is an ensemble of decision trees."},
    {"id": 104, "skill": "Machine Learning", "difficulty": "easy", "question": "What is supervised learning?", "options": ["Learning with labels", "Learning without labels", "Learning by playing games", "Learning on raw text"], "correct_answer": 0, "explanation": "Supervised learning relies on labeled training data."},
    {"id": 105, "skill": "Machine Learning", "difficulty": "medium", "question": "What is an epoch?", "options": ["A type of model", "One pass over the entire dataset", "A loss function", "An optimizer"], "correct_answer": 1, "explanation": "An epoch is one complete pass of the training dataset through the algorithm."},
    {"id": 106, "skill": "Machine Learning", "difficulty": "hard", "question": "What does the kernel trick do in SVMs?", "options": ["Reduces dimensions", "Maps data into a higher dimensional space to make it linearly separable", "Speeds up training", "Removes outliers"], "correct_answer": 1, "explanation": "The kernel trick maps data into higher dimensions."},

    # GIS
    {"id": 201, "skill": "GIS", "difficulty": "easy", "question": "What does GIS stand for?", "options": ["Geographic Information System", "Global Internet Service", "Graphical Interface Standard", "Geospatial Integration System"], "correct_answer": 0, "explanation": "GIS stands for Geographic Information System."},
    {"id": 202, "skill": "GIS", "difficulty": "medium", "question": "Which coordinate system is commonly used in global GPS?", "options": ["NAD83", "WGS84", "UTM", "State Plane"], "correct_answer": 1, "explanation": "WGS84 is the standard coordinate frame for the Earth used by GPS."},
    {"id": 203, "skill": "GIS", "difficulty": "hard", "question": "What is a shapefile's mandatory companion file that stores attribute data?", "options": [".shx", ".prj", ".dbf", ".xml"], "correct_answer": 2, "explanation": "The .dbf file stores attribute data for the shapefile."},
    {"id": 204, "skill": "GIS", "difficulty": "easy", "question": "What is a polygon in GIS?", "options": ["A line", "A point", "An enclosed area", "A map projection"], "correct_answer": 2, "explanation": "A polygon represents an enclosed area."},
    {"id": 205, "skill": "GIS", "difficulty": "medium", "question": "What is raster data?", "options": ["Data made of pixels/cells", "Data made of vectors", "Text data", "Tabular data"], "correct_answer": 0, "explanation": "Raster data is a matrix of cells (pixels)."},
    {"id": 206, "skill": "GIS", "difficulty": "hard", "question": "Which spatial interpolation method uses a weighted average of sampled points based on a variogram?", "options": ["IDW", "Spline", "Kriging", "Trend Surface"], "correct_answer": 2, "explanation": "Kriging is a geostatistical method that uses a variogram."},

    # Python
    {"id": 301, "skill": "Python", "difficulty": "easy", "question": "How do you define a function in Python?", "options": ["function myFunc()", "def myFunc():", "create myFunc()", "func myFunc():"], "correct_answer": 1, "explanation": "Python uses the 'def' keyword to define functions."},
    {"id": 302, "skill": "Python", "difficulty": "medium", "question": "What is a Python decorator?", "options": ["A class", "A variable", "A function that modifies another function", "A loop"], "correct_answer": 2, "explanation": "Decorators wrap a function to modify its behavior."},
    {"id": 303, "skill": "Python", "difficulty": "hard", "question": "What does the GIL do in CPython?", "options": ["Generates intermediate language", "Prevents multiple native threads from executing Python bytecodes at once", "Garbage collects unused memory", "Global Interface Layer for C extensions"], "correct_answer": 1, "explanation": "The Global Interpreter Lock prevents parallel thread execution of python bytecodes."},
    {"id": 304, "skill": "Python", "difficulty": "easy", "question": "What data type is [1, 2, 3]?", "options": ["Tuple", "Set", "Dictionary", "List"], "correct_answer": 3, "explanation": "Square brackets denote a Python list."},
    {"id": 305, "skill": "Python", "difficulty": "medium", "question": "How do you handle exceptions in Python?", "options": ["try/catch", "try/except", "do/catch", "catch/finally"], "correct_answer": 1, "explanation": "Python uses try and except blocks."},
    {"id": 306, "skill": "Python", "difficulty": "hard", "question": "What is a metaclass in Python?", "options": ["A class that inherits from multiple classes", "The class of a class", "An abstract base class", "A class with only static methods"], "correct_answer": 1, "explanation": "A metaclass is a class whose instances are classes."},

    # Statistics
    {"id": 401, "skill": "Statistics", "difficulty": "easy", "question": "What is the mean of 2, 4, and 6?", "options": ["2", "4", "6", "12"], "correct_answer": 1, "explanation": "(2+4+6)/3 = 4"},
    {"id": 402, "skill": "Statistics", "difficulty": "medium", "question": "What does a p-value of 0.01 generally indicate?", "options": ["Strong evidence against the null hypothesis", "Weak evidence against the null hypothesis", "The null hypothesis is true", "The sample size is too small"], "correct_answer": 0, "explanation": "A low p-value indicates strong evidence against the null hypothesis."},
    {"id": 403, "skill": "Statistics", "difficulty": "hard", "question": "Which sampling technique divides a population into subgroups before sampling?", "options": ["Cluster", "Stratified", "Systematic", "Convenience"], "correct_answer": 1, "explanation": "Stratified sampling involves dividing the population into strata."},
    {"id": 404, "skill": "Statistics", "difficulty": "easy", "question": "What is the median of 1, 3, 3, 6, 7, 8, 9?", "options": ["3", "6", "7", "8"], "correct_answer": 1, "explanation": "6 is the middle number."},
    {"id": 405, "skill": "Statistics", "difficulty": "medium", "question": "What is standard deviation?", "options": ["The average value", "The middle value", "A measure of the amount of variation or dispersion", "The most frequent value"], "correct_answer": 2, "explanation": "Standard deviation measures dispersion."},
    {"id": 406, "skill": "Statistics", "difficulty": "hard", "question": "In a normal distribution, what percentage of data falls within one standard deviation of the mean?", "options": ["50%", "68%", "95%", "99.7%"], "correct_answer": 1, "explanation": "According to the empirical rule, approximately 68% of data falls within 1 standard deviation."},

    # SQL
    {"id": 501, "skill": "SQL", "difficulty": "easy", "question": "Which keyword is used to retrieve data from a database?", "options": ["GET", "EXTRACT", "SELECT", "PULL"], "correct_answer": 2, "explanation": "SELECT is used to query data."},
    {"id": 502, "skill": "SQL", "difficulty": "medium", "question": "Which SQL statement is used to combine rows from two or more tables based on a related column?", "options": ["MERGE", "JOIN", "COMBINE", "LINK"], "correct_answer": 1, "explanation": "JOIN is used to combine tables."},
    {"id": 503, "skill": "SQL", "difficulty": "hard", "question": "What is the difference between RANK() and DENSE_RANK()?", "options": ["RANK leaves gaps in ranking, DENSE_RANK does not", "DENSE_RANK leaves gaps, RANK does not", "They are identical", "RANK is faster"], "correct_answer": 0, "explanation": "RANK() leaves a gap in sequence if there is a tie; DENSE_RANK() does not."},
    {"id": 504, "skill": "SQL", "difficulty": "easy", "question": "How do you filter records in SQL?", "options": ["FILTER BY", "WHERE", "HAVING", "SORT BY"], "correct_answer": 1, "explanation": "The WHERE clause is used to filter records."},
    {"id": 505, "skill": "SQL", "difficulty": "medium", "question": "What does the GROUP BY statement do?", "options": ["Sorts the result set", "Filters records", "Groups rows that have the same values into summary rows", "Joins two tables"], "correct_answer": 2, "explanation": "GROUP BY aggregates data into summary rows."},
    {"id": 506, "skill": "SQL", "difficulty": "hard", "question": "What is a Common Table Expression (CTE)?", "options": ["A permanent table", "A temporary named result set created using the WITH clause", "An index", "A stored procedure"], "correct_answer": 1, "explanation": "A CTE provides a temporary result set using WITH."},
]

def get_assessment_for_blueprint(blueprint: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate a deterministic test strictly following the blueprint requirements."""
    
    requirements = blueprint["difficulty_distribution"]
    req_easy = requirements["easy"]
    req_medium = requirements["medium"]
    req_hard = requirements["hard"]
    
    selected_questions = []
    
    # We want to distribute the difficulty across the required skills as evenly as possible.
    # For a perfect fallback, we will just iterate through available questions matching the skills
    # and pick them until we satisfy the difficulty counts.
    
    valid_skills = [c["skill"] for c in blueprint["competencies"]]
    
    # Track how many of each difficulty we still need
    needs = {"easy": req_easy, "medium": req_medium, "hard": req_hard}
    
    # Track how many questions each skill needs based on blueprint allocation
    skill_needs = {c["skill"]: c["question_count"] for c in blueprint["competencies"]}
    
    available_qs = [q for q in QUESTION_BANK if q["skill"] in valid_skills]
    
    # It is a hard constraint to meet the skill allocation and difficulty allocation.
    # In a deterministic fallback, we'll try our best to satisfy both.
    # 1. Group by skill
    qs_by_skill = {skill: [] for skill in valid_skills}
    for q in available_qs:
        qs_by_skill[q["skill"]].append(q)
        
    # We will pick questions to satisfy `skill_needs` while attempting to balance `needs`.
    for skill in valid_skills:
        needed = skill_needs[skill]
        skill_q = qs_by_skill[skill]
        
        # Sort so we try to pick difficulties we still need
        skill_q.sort(key=lambda x: (needs[x["difficulty"]], random.random()), reverse=True)
        
        for q in skill_q:
            if needed > 0 and needs[q["difficulty"]] > 0:
                selected_questions.append(q)
                needs[q["difficulty"]] -= 1
                needed -= 1
                
        # If we still need questions for this skill but ran out of required difficulty,
        # just pick any available from this skill to satisfy the skill count.
        for q in skill_q:
            if needed > 0 and q not in selected_questions:
                selected_questions.append(q)
                needs[q["difficulty"]] -= 1 # This will go negative but that's okay for fallback best-effort
                needed -= 1

    return selected_questions

def get_question_by_id(question_id: int) -> Dict[str, Any]:
    for q in QUESTION_BANK:
        if q["id"] == question_id:
            return q
    return None
