import { api } from "./api";
import { PersonalizedRecommendationResponse, PersonalizedItemResponse } from "../types/recommendation";

export interface RecommendationFilters {
  priority?: string;
  provider?: string;
  competency?: string;
  limit?: number;
  debug?: boolean;
}

export const recommendationApi = {
  getRecommendations: async (
    userId: string, 
    filters: RecommendationFilters = {}
  ): Promise<PersonalizedRecommendationResponse> => {
    let path = `/users/${userId}/recommendations?`;
    const params = new URLSearchParams();
    if (filters.priority) params.append("priority", filters.priority);
    if (filters.provider) params.append("provider", filters.provider);
    if (filters.competency) params.append("competency", filters.competency);
    if (filters.limit) params.append("limit", String(filters.limit));
    if (filters.debug) params.append("debug", "true");
    
    return api.get<PersonalizedRecommendationResponse>(path + params.toString());
  },
  
  refreshRecommendations: async (userId: string): Promise<PersonalizedRecommendationResponse> => {
    return api.post<PersonalizedRecommendationResponse>(`/users/${userId}/recommendations/refresh`);
  },
  
  getCompetencyRecommendations: async (
    userId: string, 
    competencyId: string
  ): Promise<PersonalizedItemResponse[]> => {
    return api.get<PersonalizedItemResponse[]>(`/users/${userId}/competencies/${competencyId}/recommendations`);
  }
};
