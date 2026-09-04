import { api } from "./api";
import { UserProfile } from "../types/auth";

export interface ProfileUpdateRequest {
  first_name?: string;
  last_name?: string;
  designation?: string;
  department?: string;
  job_role_id?: string;
  contact_number?: string;
  bio?: string;
}

export interface ReadinessMetrics {
  overall_readiness: number;
  competencies_assessed: number;
  high_priority_gaps: number;
  medium_priority_gaps: number;
  low_priority_gaps: number;
}

export interface CompetencyEvidenceLog {
  id: string;
  user_competency_id: string;
  evidence_type: string;
  title: string;
  description?: string;
  evidence_url?: string;
  verified: boolean;
  verified_by?: string;
  created_at: string;
}

export const userApi = {
  getProfile: async (userId: string): Promise<UserProfile> => {
    return api.get<UserProfile>(`/users/${userId}/profile`);
  },

  updateProfile: async (userId: string, data: ProfileUpdateRequest): Promise<UserProfile> => {
    return api.put<UserProfile>(`/users/${userId}/profile`, data);
  },

  getReadinessScore: async (userId: string): Promise<ReadinessMetrics> => {
    return api.get<ReadinessMetrics>(`/users/${userId}/readiness-score`);
  },

  getUserEvidence: async (userId: string): Promise<CompetencyEvidenceLog[]> => {
    return api.get<CompetencyEvidenceLog[]>(`/users/${userId}/evidence`);
  }
};
