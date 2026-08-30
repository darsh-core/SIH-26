from abc import ABC, abstractmethod

class SemanticScorer(ABC):
    
    @abstractmethod
    def calculate_similarity(self, text: str, query: str) -> float:
        """
        Calculates semantic similarity score between 0.0 and 1.0.
        """
        pass


class MockSemanticScorer(SemanticScorer):
    
    def calculate_similarity(self, text: str, query: str) -> float:
        """
        Deterministic keyword overlap similarity index representing semantic scoring.
        """
        if not text or not query:
            return 0.5
            
        t_lower = text.lower()
        q_lower = query.lower()
        
        # 1. Exact match boost
        if q_lower in t_lower:
            return 1.0
            
        # 2. Token overlap search
        stopwords = {"and", "of", "the", "in", "to", "for", "on", "with", "a", "an", "statistics", "methodology"}
        q_words = [w for w in q_lower.replace("/", " ").replace("_", " ").split() if w not in stopwords]
        
        if not q_words:
            return 0.5
            
        matches = 0
        for w in q_words:
            if w in t_lower:
                matches += 1
                
        similarity = matches / len(q_words)
        # Scale to 0.2 - 0.9 range for mock realism
        return max(0.2, min(0.9, 0.2 + similarity * 0.7))
