import { api } from "./api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface CopilotCitation {
  document_id: string;
  document_title: string;
  document_filename: string;
  page?: number | null;
  slide?: number | null;
  source_type: string;
  text_snippet: string;
  similarity: number;
}

export interface CopilotChatResponse {
  reply: string;
  citations: CopilotCitation[];
  model: string;
  grounded: boolean;
  session_id: string;
}

export interface CopilotChatRequest {
  message: string;
  user_id?: string;
  context_type?: string;
  resource_id?: string;
  document_id?: string;
  competency_id?: string;
  session_id?: string;
  history?: ChatMessage[];
}

export interface QuickPrompt {
  title: string;
  prompt: string;
  category: string;
  icon?: string;
}

export const copilotApi = {
  chat: (payload: CopilotChatRequest) => 
    api.post<CopilotChatResponse>("/copilot/chat", payload),
  getQuickPrompts: () => 
    api.get<QuickPrompt[]>("/copilot/quick-prompts")
};
