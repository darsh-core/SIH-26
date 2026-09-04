export interface UserRole {
  id: string;
  name: string;
  description?: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  designation?: string;
  department?: string;
  job_role_id?: string;
  domain?: string;
  contact_number?: string;
  bio?: string;
}

export interface AppUser {
  id: string;
  email: string;
  is_active: boolean;
  is_superuser?: boolean;
  roles: UserRole[];
  profile?: UserProfile;
}

export interface AuthState {
  access_token: string | null;
  refresh_token: string | null;
  user: AppUser | null;
}
