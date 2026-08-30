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
  }
};
