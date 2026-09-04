import { api } from "./api";
import { JobRole } from "../types/competency";

export interface RoleCompetencyItem {
  competency_id: string;
  competency_code: string;
  competency_name: string;
  required_level: number;
  weight: number;
  is_mandatory: boolean;
}

export interface RoleCompetencyResponse {
  role_id: string;
  role_name: string;
  role_code: string;
  competencies: RoleCompetencyItem[];
}

export const roleApi = {
  getRoles: async (): Promise<JobRole[]> => {
    return api.get<JobRole[]>("/roles");
  },

  getRole: async (roleId: string): Promise<JobRole> => {
    return api.get<JobRole>(`/roles/${roleId}`);
  },

  getRoleCompetencies: async (roleId: string): Promise<RoleCompetencyResponse> => {
    return api.get<RoleCompetencyResponse>(`/roles/${roleId}/competencies`);
  }
};
