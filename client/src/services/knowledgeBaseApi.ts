import api from "./api";
import type {
  KnowledgeBaseUploadResponse,
  KnowledgeBaseStatusResponse,
  KnowledgeBaseListResponse,
  KnowledgeBaseDocument,
  AgentKnowledgeBaseResponse,
} from "@/types/knowledge-base.types";

export const knowledgeBaseApi = {
  /**
   * Upload a document to the knowledge base, trigger RAG indexing,
   * and attach it to the configured agent.
   * Returns immediately after upload starts - use getIndexingStatus to poll for completion.
   */
  uploadDocument: async (file: File): Promise<KnowledgeBaseUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<KnowledgeBaseUploadResponse>(
      "/api/knowledge-base/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },

  /**
   * Get the current RAG indexing status for a document.
   * Poll this endpoint to track indexing progress.
   */
  getIndexingStatus: async (documentId: string): Promise<KnowledgeBaseStatusResponse> => {
    const response = await api.get<KnowledgeBaseStatusResponse>(
      `/api/knowledge-base/status/${documentId}`
    );
    return response.data;
  },

  /**
   * List all documents in the account's knowledge base.
   */
  listDocuments: async (
    pageSize: number = 50,
    search?: string
  ): Promise<KnowledgeBaseListResponse> => {
    const params: Record<string, string | number> = { page_size: pageSize };
    if (search) {
      params.search = search;
    }

    const response = await api.get<KnowledgeBaseListResponse>("/api/knowledge-base/documents", {
      params,
    });
    return response.data;
  },

  /**
   * List documents attached to the agent's knowledge base.
   * These are the documents actively used by the agent for RAG.
   */
  getAgentDocuments: async (): Promise<AgentKnowledgeBaseResponse> => {
    const response = await api.get<AgentKnowledgeBaseResponse>(
      "/api/knowledge-base/agent-documents"
    );
    return response.data;
  },

  /**
   * Get details of a specific document.
   */
  getDocument: async (documentId: string): Promise<KnowledgeBaseDocument> => {
    const response = await api.get<KnowledgeBaseDocument>(
      `/api/knowledge-base/document/${documentId}`
    );
    return response.data;
  },
};
