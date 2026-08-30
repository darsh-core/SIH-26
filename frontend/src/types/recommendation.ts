export interface TargetCompetencyDetail {
  code: string;
  current_level: number;
  required_level: number;
  gap: number;
}

export interface DebugScores {
  competency_match: number;
  semantic_similarity: number;
  difficulty_fit: number;
  duration_fit: number;
  provider_quality: number;
  recency: number;
  raw_score: number;
  final_score: number;
}

export interface PersonalizedItemResponse {
  resource_id: string;
  provider: "iGOT" | "NSSTA";
  title: string;
  resource_type: "COURSE" | "TRAINING_PROGRAM";
  target_competencies: TargetCompetencyDetail[];
  score: number;
  priority: "HIGH" | "MEDIUM" | "LOW" | "NONE";
  reason: string;
  estimated_duration_minutes: number;
  difficulty: "Beginner" | "Intermediate" | "Advanced";
  debug_scores?: DebugScores | null;
}

export interface PersonalizedRecommendationResponse {
  user_id: string;
  role: string;
  overall_readiness: number;
  recommendations: PersonalizedItemResponse[];
}
