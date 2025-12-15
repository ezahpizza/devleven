// Knowledge Base / RAG Types

export type RAGIndexingStatus =
  | "created"
  | "processing"
  | "failed"
  | "succeeded"
  | "rag_limit_exceeded"
  | "document_too_small"
  | "cannot_index_folder";

export interface KnowledgeBaseDocument {
  id: string;
  name: string;
  type: "file" | "url" | "text" | "folder";
  created_at: number | null;
  size_bytes: number | null;
  supported_usages: string[];
}

export interface AgentKnowledgeBaseDocument {
  id: string;
  name: string;
  type: "file" | "url" | "text";
}

export interface KnowledgeBaseUploadResponse {
  success: boolean;
  message: string;
  document_id: string;
  document_name: string;
  indexing_status: RAGIndexingStatus;
  progress_percentage: number;
  attached_to_agent: boolean;
  agent_id?: string;
  agent_attachment_error?: string;
}

export interface KnowledgeBaseStatusResponse {
  document_id: string;
  status: RAGIndexingStatus;
  progress_percentage: number;
  model?: string;
}

export interface KnowledgeBaseListResponse {
  documents: KnowledgeBaseDocument[];
  has_more: boolean;
}

export interface AgentKnowledgeBaseResponse {
  agent_id: string;
  documents: AgentKnowledgeBaseDocument[];
  count: number;
}

export interface KnowledgeBaseWebSocketMessage {
  event: "knowledge_base_upload";
  data: {
    document_id: string;
    document_name: string;
    status: RAGIndexingStatus;
    progress: number;
    attached_to_agent: boolean;
  };
}

// Upload state for tracking progress in UI
export interface DocumentUploadState {
  file: File | null;
  isUploading: boolean;
  uploadProgress: number;
  documentId: string | null;
  documentName: string | null;
  indexingStatus: RAGIndexingStatus | null;
  indexingProgress: number;
  attachedToAgent: boolean;
  agentId: string | null;
  error: string | null;
}

export const ALLOWED_FILE_TYPES = [".pdf", ".txt", ".doc", ".docx", ".md"];
export const MAX_FILE_SIZE_MB = 50;
