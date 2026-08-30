export interface CompetencyLevel {
  id: string;
  competency_id: string;
  level_number: number;
  name: string;
  description: string;
}

export interface Competency {
  id: string;
  framework_id: string;
  name: string;
  code: string;
  description?: string;
  levels?: CompetencyLevel[];
}

export interface CompetencyEvidence {
  id: string;
  user_competency_id: string;
  evidence_type: string;  // ASSESSMENT, CERTIFICATE, WORK_ITEM
  title: string;
  description?: string;
  evidence_url?: string;
  verified: boolean;
  verified_by?: string;
  created_at: string;
}

export interface UserCompetency {
  id: string;
  user_id: string;
  competency_id: string;
  current_level: number;
  status: string;
  updated_at: string;
  competency?: Competency;
  evidences?: CompetencyEvidence[];
}

export interface RoleCompetency {
  id: string;
  job_role_id: string;
  competency_id: string;
  required_level: number;
  weight: number;
  is_mandatory: boolean;
  competency?: Competency;
}

export interface JobRole {
  id: string;
  name: string;
  code: string;
  description?: string;
  competency_requirements?: RoleCompetency[];
}

export interface CompetencyGapDetail {
  competency_id: string;
  competency_code: string;
  competency_name: string;
  required_level: number;
  current_level: number;
  gap: number;
  normalized_gap: number;
  priority: "HIGH" | "MEDIUM" | "LOW" | "NONE";
  mandatory: boolean;
  weight: number;
}

export interface UserCompetencyGapsResponse {
  user_id: string;
  role: {
    id: string;
    name: string;
    code: string;
  };
  overall_readiness: number;
  gaps: CompetencyGapDetail[];
}
