import { api } from "./api";
import { Competency, UserCompetencyGapsResponse, UserCompetency } from "../types/competency";

export interface PaginatedCompetencies {
  items: Competency[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export const competencyApi = {
  getCompetencies: async (framework?: string, search?: string): Promise<PaginatedCompetencies> => {
    let path = "/competencies?size=100";
    if (framework) path += `&framework=${encodeURIComponent(framework)}`;
    if (search) path += `&search=${encodeURIComponent(search)}`;
    return api.get<PaginatedCompetencies>(path);
  },
  
  getCompetency: async (id: string): Promise<Competency> => {
    return api.get<Competency>(`/competencies/${id}`);
  },
  
  getCompetencyGaps: async (userId: string): Promise<UserCompetencyGapsResponse> => {
    return api.get<UserCompetencyGapsResponse>(`/users/${userId}/competency-gaps`);
  },
  
  getUserCompetencies: async (userId: string): Promise<UserCompetency[]> => {
    return api.get<UserCompetency[]>(`/users/${userId}/competencies`);
  }
};
