export interface Course {
  id: string;
  provider_id: string;
  code: string;
  title: string;
  description?: string;
  duration_minutes: number;
  difficulty: string;
  language?: string;
  url?: string;
}

export interface TrainingProgram {
  id: string;
  provider_id: string;
  code: string;
  title: string;
  description?: string;
  duration_days: number;
  mode: string;
  location?: string;
}

export interface LearningProgress {
  id: string;
  user_id: string;
  item_type: "COURSE" | "TRAINING_PROGRAM";
  course_id?: string;
  training_program_id?: string;
  progress_percentage: number;
  status: "ENROLLED" | "IN_PROGRESS" | "COMPLETED";
  last_accessed?: string;
}

export interface LearningPlanItem {
  id: string;
  learning_plan_id: string;
  item_type: "COURSE" | "TRAINING_PROGRAM";
  course_id?: string;
  training_program_id?: string;
  sequence_order: number;
  status: "PENDING" | "COMPLETED";
  course?: Course;
  training_program?: TrainingProgram;
}

export interface LearningPlan {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  status: "ACTIVE" | "COMPLETED" | "ARCHIVED";
  created_at: string;
  items: LearningPlanItem[];
}
