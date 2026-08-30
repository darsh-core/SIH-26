export interface AssessmentOption {
  id: string;
  question_id: string;
  option_text: string;
}

export interface AssessmentQuestion {
  id: string;
  assessment_id: string;
  question_text: string;
  competency_id: string;
  target_level: number;
  options: AssessmentOption[];
}

export interface Assessment {
  id: string;
  title: string;
  description?: string;
  competency_id: string;
  target_level: number;
  questions?: AssessmentQuestion[];
}

export interface AssessmentAttempt {
  id: string;
  assessment_id: string;
  user_id: string;
  score?: number;
  passed?: boolean;
  status: "STARTED" | "COMPLETED";
  started_at: string;
  completed_at?: string;
}

export interface AssessmentResultResponse {
  attempt_id: string;
  score: number;
  passed: boolean;
  accuracy_by_competency: Record<string, number>;
  levels_updated: Record<string, { before: number; after: number; gained: number }>;
}
