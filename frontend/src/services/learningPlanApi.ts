import { api } from "./api";
import { LearningPlan, LearningPlanItem } from "../types/learning";

export const learningPlanApi = {
  generateLearningPlan: async (userId: string): Promise<LearningPlan> => {
    return api.post<LearningPlan>(`/users/${userId}/learning-plans/generate`);
  },
  
  getLearningPlans: async (userId: string): Promise<LearningPlan[]> => {
    return api.get<LearningPlan[]>(`/users/${userId}/learning-plans`);
  },
  
  getLearningPlan: async (id: string): Promise<LearningPlan> => {
    return api.get<LearningPlan>(`/learning-plans/${id}`);
  },
  
  deletePlanItem: async (planId: string, itemId: string): Promise<void> => {
    return api.delete<void>(`/learning-plans/${planId}/items/${itemId}`);
  }
};
