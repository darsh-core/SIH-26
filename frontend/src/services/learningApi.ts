import { api } from "./api";

export interface LearningCompetencyDetail {
  code: string;
  name: string;
  target_level: number;
  weight: number;
}

export interface LearningLessonDetail {
  id: string;
  title: string;
  content: string;
  duration_minutes: number;
  sequence_order: number;
}

export interface LearningModuleDetail {
  id: string;
  code: string;
  title: string;
  description?: string;
  duration_minutes: number;
  sequence_order: number;
  is_required: boolean;
  lessons: LearningLessonDetail[];
}

export interface NormalizedLearningResource {
  id: string;
  provider: string;
  provider_name: string;
  external_course_id: string;
  title: string;
  description?: string;
  duration_minutes: number;
  difficulty: string;
  language: string;
  course_url?: string;
  is_demo: boolean;
  competencies: LearningCompetencyDetail[];
  modules: LearningModuleDetail[];
  metadata_json?: Record<string, any>;
}

export interface ModuleProgressStatus {
  module_id: string;
  module_code: string;
  module_title: string;
  sequence_order: number;
  status: "NOT_STARTED" | "IN_PROGRESS" | "COMPLETED";
  completed_at?: string | null;
}

export interface LearningProgressDetail {
  enrollment_id: string;
  user_id: string;
  course_id: string;
  external_course_id: string;
  course_title: string;
  provider_name: string;
  is_demo: boolean;
  progress_percentage: number;
  status: "ENROLLED" | "IN_PROGRESS" | "COMPLETED";
  completed_modules: number;
  total_modules: number;
  modules: ModuleProgressStatus[];
  enrolled_at: string;
  completion_date?: string | null;
}

export interface CourseLaunchResponse {
  provider: string;
  is_demo: boolean;
  course_id: string;
  external_course_id: string;
  course_title: string;
  launch_url: string;
}

export interface LearningEnrollmentResponse {
  enrollment_id: string;
  user_id: string;
  course_id: string;
  external_course_id: string;
  course_title: string;
  status: string;
  progress_percentage: number;
  enrolled_at: string;
  message: string;
}

export interface LearningHistoryItem {
  enrollment_id: string;
  course_id: string;
  external_course_id: string;
  title: string;
  provider: string;
  provider_name: string;
  difficulty: string;
  duration_minutes: number;
  progress_percentage: number;
  status: string;
  enrolled_at: string;
  completed_at?: string | null;
  is_demo: boolean;
}

export interface ProviderInfo {
  code: string;
  name: string;
  provider_type: "DEMO" | "LIVE";
  description: string;
  is_active: boolean;
  is_configured: boolean;
}

export const learningApi = {
  getProviders: async (): Promise<ProviderInfo[]> => {
    return api.get<ProviderInfo[]>("/learning/providers");
  },

  getCourses: async (params?: { competency?: string; difficulty?: string }): Promise<NormalizedLearningResource[]> => {
    const searchParams = new URLSearchParams();
    if (params?.competency) searchParams.append("competency", params.competency);
    if (params?.difficulty) searchParams.append("difficulty", params.difficulty);
    const query = searchParams.toString() ? `?${searchParams.toString()}` : "";
    return api.get<NormalizedLearningResource[]>(`/learning/courses${query}`);
  },

  getCourse: async (courseId: string): Promise<NormalizedLearningResource> => {
    return api.get<NormalizedLearningResource>(`/learning/courses/${courseId}`);
  },

  enrollCourse: async (courseId: string): Promise<LearningEnrollmentResponse> => {
    return api.post<LearningEnrollmentResponse>(`/learning/courses/${courseId}/enroll`);
  },

  launchCourse: async (courseId: string): Promise<CourseLaunchResponse> => {
    return api.post<CourseLaunchResponse>(`/learning/courses/${courseId}/launch`);
  },

  getProgress: async (courseId: string): Promise<LearningProgressDetail> => {
    return api.get<LearningProgressDetail>(`/learning/courses/${courseId}/progress`);
  },

  completeModule: async (courseId: string, moduleId: string): Promise<LearningProgressDetail> => {
    return api.post<LearningProgressDetail>(`/learning/courses/${courseId}/modules/${moduleId}/complete`);
  },

  completeCourse: async (courseId: string): Promise<LearningProgressDetail> => {
    return api.post<LearningProgressDetail>(`/learning/courses/${courseId}/complete`);
  },

  getLearningHistory: async (): Promise<LearningHistoryItem[]> => {
    return api.get<LearningHistoryItem[]>("/learning/history");
  },
};
