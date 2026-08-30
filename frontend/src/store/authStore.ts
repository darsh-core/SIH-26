import { create } from "zustand"
import { AppUser } from "../types/auth"

interface AuthStore {
  accessToken: string | null;
  refreshToken: string | null;
  user: AppUser | null;
  isAuthenticated: boolean;
  setAuth: (accessToken: string, refreshToken: string, user: AppUser) => void;
  updateUser: (user: AppUser) => void;
  clearAuth: () => void;
}

const getStoredAuth = () => {
  try {
    if (typeof localStorage !== "undefined") {
      const token = localStorage.getItem("token");
      const refresh = localStorage.getItem("refresh_token");
      const userStr = localStorage.getItem("user");
      
      if (token && userStr) {
        return {
          accessToken: token,
          refreshToken: refresh,
          user: JSON.parse(userStr),
          isAuthenticated: true
        };
      }
    }
  } catch (e) {
    console.error("Error reading initial auth storage:", e);
  }
  
  return {
    accessToken: null,
    refreshToken: null,
    user: null,
    isAuthenticated: false
  };
};

const initialAuth = getStoredAuth();

export const useAuthStore = create<AuthStore>((set) => ({
  ...initialAuth,
  setAuth: (accessToken, refreshToken, user) => {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("token", accessToken);
      localStorage.setItem("refresh_token", refreshToken);
      localStorage.setItem("user", JSON.stringify(user));
    }
    set({ accessToken, refreshToken, user, isAuthenticated: true });
  },
  updateUser: (user) => {
    if (typeof localStorage !== "undefined") {
      localStorage.setItem("user", JSON.stringify(user));
    }
    set({ user });
  },
  clearAuth: () => {
    if (typeof localStorage !== "undefined") {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("user");
    }
    set({ accessToken: null, refreshToken: null, user: null, isAuthenticated: false });
  }
}));
