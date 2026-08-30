export const API_BASE_URL = 
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_BASE_URL) || "http://127.0.0.1:8000/api/v1";

export const DEMO_MODE = 
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_DEMO_MODE === "true") || true; // default to true in dev for convenience

export const DEMO_CREDENTIALS = {
  email: "employee@mospi.gov.in",
  password: "password123"
};

export const DOMAIN_LABELS: Record<string, string> = {
  STATISTICAL: "Statistical Domain",
  TECHNICAL: "Technical Domain",
  DIGITAL_GOVERNANCE: "Digital Governance",
  BEHAVIOURAL: "Behavioural Competency"
};

export const PRIORITY_COLORS = {
  HIGH: "bg-red-50 text-red-700 border-red-200",
  MEDIUM: "bg-amber-50 text-amber-700 border-amber-200",
  LOW: "bg-blue-50 text-blue-700 border-blue-200",
  NONE: "bg-slate-50 text-slate-700 border-slate-200"
};
