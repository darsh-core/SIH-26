import { api } from "./api";
import { Assessment, AssessmentAttempt, AssessmentResultResponse } from "../types/assessment";

export interface SubmitAnswerItem {
  question_id: string;
  selected_option_id: string;
}

export interface PaginatedAssessments {
  items: Assessment[];
  total: number;
}

export const assessmentApi = {
  getAssessments: async (): Promise<PaginatedAssessments> => {
    return api.get<PaginatedAssessments>("/assessments?size=10");
  },

  getAssessment: async (id: string): Promise<Assessment> => {
    return api.get<Assessment>(`/assessments/${id}`);
  },
  
  startAttempt: async (assessmentId: string): Promise<any> => {
    return api.post<any>(`/assessments/${assessmentId}/start`);
  },
  
  submitAnswers: async (
    assessmentId: string,
    attemptId: string, 
    answers: SubmitAnswerItem[]
  ): Promise<AssessmentResultResponse> => {
    return api.post<AssessmentResultResponse>(`/assessments/${assessmentId}/submit?attempt_id=${attemptId}`, {
      answers
    });
  },

  createRoleDiagnostic: async (jobRoleId: string, questionCount: number = 6): Promise<{
    assessment_id: string;
    title: string;
    total_questions: number;
    competency_breakdown: string[];
  }> => {
    return api.post("/assessments/role-diagnostic", {
      job_role_id: jobRoleId,
      question_count: questionCount
    });
  },

  getAssessmentResults: async (assessmentId: string, attemptId?: string): Promise<AssessmentResultResponse> => {
    const url = `/assessments/${assessmentId}/results${attemptId ? `?attempt_id=${attemptId}` : ''}`;
    return api.get<AssessmentResultResponse>(url);
  }
};
