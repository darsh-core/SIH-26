import { api } from "./api"

export interface DocumentItem {
  id: string;
  title: string;
  filename: string;
  file_type: string;
  status: string;
  chunk_count: number;
  upload_date: string;
}

export interface DocumentDetails extends DocumentItem {
  detected_competencies: Array<{
    competency_id: string;
    competency_code: string;
    competency_name: string;
    confidence: number;
    mapping_method: string;
  }>;
  metadata: any;
}

export interface GeneratedMCQ {
  question: string;
  options: Array<{ text: string }>;
  correct_answer: number;
  explanation: string;
  competency_code: string;
  difficulty: string;
  confidence: number;
  source_page: number;
  grounding_score: number;
  source_chunk_ids: string[];
}

export const documentApi = {
  listDocuments: (page: number = 1, size: number = 10) =>
    api.get<{ items: DocumentItem[]; total: number; page: number; size: number }>(
      `/documents?page=${page}&size=${size}`
    ),

  getDocument: (id: string) =>
    api.get<DocumentDetails>(`/documents/${id}`),

  uploadDocument: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.postFormData<any>("/documents", formData);
  },

  searchSimilarChunks: (query: string, topK: number = 5) =>
    api.post<any>("/documents/search", { query, top_k: topK }),

  generateMCQs: (
    documentId: string,
    params: { competency_id: string; difficulty: string; count: number }
  ) =>
    api.post<{
      document_id: string;
      competency: string;
      generated: number;
      accepted: number;
      rejected: number;
      questions: GeneratedMCQ[];
    }>(`/documents/${documentId}/generate-mcqs`, params),

  generateAssessment: (
    documentId: string,
    params: { competency_id: string; question_count: number; difficulty: string }
  ) =>
    api.post<{
      assessment_id: string;
      title: string;
      question_count: number;
      competency: string;
      difficulty: string;
    }>(`/documents/${documentId}/generate-assessment`, params)
}
