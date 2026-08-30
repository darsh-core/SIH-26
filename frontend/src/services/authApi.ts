import { api } from "./api";
import { AppUser } from "../types/auth";
import { API_BASE_URL } from "../lib/constants";

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
}

export const authApi = {
  login: async (email: string, password: string): Promise<LoginResponse> => {
    return api.post<LoginResponse>("/auth/login", { email, password });
  },
  
  getMe: async (): Promise<AppUser> => {
    return api.get<AppUser>("/auth/me");
  }
};
