import { useState, useRef, useCallback, useEffect } from "react";
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2, BookOpen, Bot } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { knowledgeBaseApi } from "@/services/knowledgeBaseApi";
import { toast } from "sonner";
import type {
  RAGIndexingStatus,
  DocumentUploadState,
} from "@/types/knowledge-base.types";
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE_MB } from "@/types/knowledge-base.types";

interface KnowledgeBaseUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const POLL_INTERVAL_MS = 3000;
const MAX_POLL_ATTEMPTS = 100; // ~5 minutes max

const initialState: DocumentUploadState = {
  file: null,
  isUploading: false,
  uploadProgress: 0,
  documentId: null,
  documentName: null,
  indexingStatus: null,
  indexingProgress: 0,
  attachedToAgent: false,
  agentId: null,
  error: null,
};

export const KnowledgeBaseUploadModal = ({
  isOpen,
  onClose,
  onSuccess,
}: KnowledgeBaseUploadModalProps) => {
  const [state, setState] = useState<DocumentUploadState>(initialState);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pollAttemptsRef = useRef(0);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  const resetState = useCallback(() => {
    if (pollTimeoutRef.current) {
      clearTimeout(pollTimeoutRef.current);
    }
    pollAttemptsRef.current = 0;
    setState(initialState);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  const handleClose = useCallback(() => {
    if (!state.isUploading && state.indexingStatus !== "processing") {
      resetState();
      onClose();
    }
  }, [state.isUploading, state.indexingStatus, resetState, onClose]);

  const validateFile = (file: File): string | null => {
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    if (!ALLOWED_FILE_TYPES.includes(ext)) {
      return `Invalid file type. Allowed: ${ALLOWED_FILE_TYPES.join(", ")}`;
    }

    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > MAX_FILE_SIZE_MB) {
      return `File too large. Maximum size: ${MAX_FILE_SIZE_MB}MB`;
    }

    return null;
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const error = validateFile(file);
    if (error) {
      setState((prev) => ({ ...prev, error }));
      toast.error(error);
      return;
    }

    setState((prev) => ({
      ...prev,
      file,
      error: null,
    }));
  };

  const pollIndexingStatus = useCallback(async (documentId: string) => {
    if (pollAttemptsRef.current >= MAX_POLL_ATTEMPTS) {
      setState((prev) => ({
        ...prev,
        error: "Indexing timed out. The document may still be processing.",
        indexingStatus: "failed" as RAGIndexingStatus,
      }));
      return;
    }

    try {
      pollAttemptsRef.current++;
      const status = await knowledgeBaseApi.getIndexingStatus(documentId);

      setState((prev) => ({
        ...prev,
        indexingStatus: status.status,
        indexingProgress: status.progress_percentage,
      }));

      if (status.status === "succeeded") {
        toast.success("Document indexed successfully!");
        onSuccess?.();
        return;
      }

      if (
        status.status === "failed" ||
        status.status === "rag_limit_exceeded" ||
        status.status === "document_too_small" ||
        status.status === "cannot_index_folder"
      ) {
        const errorMsg = getStatusErrorMessage(status.status);
        setState((prev) => ({
          ...prev,
          error: errorMsg,
        }));
        toast.error(errorMsg);
        return;
      }

      // Continue polling
      pollTimeoutRef.current = setTimeout(() => {
        pollIndexingStatus(documentId);
      }, POLL_INTERVAL_MS);
    } catch (err) {
      console.error("Error polling status:", err);
      setState((prev) => ({
        ...prev,
        error: "Failed to check indexing status",
      }));
    }
  }, [onSuccess]);

  const handleUpload = async () => {
    if (!state.file) return;

    setState((prev) => ({
      ...prev,
      isUploading: true,
      uploadProgress: 10,
      error: null,
    }));

    try {
      // Simulate upload progress
      setState((prev) => ({ ...prev, uploadProgress: 30 }));

      const response = await knowledgeBaseApi.uploadDocument(state.file);

      setState((prev) => ({
        ...prev,
        isUploading: false,
        uploadProgress: 100,
        documentId: response.document_id,
        documentName: response.document_name,
        indexingStatus: response.indexing_status,
        indexingProgress: response.progress_percentage,
        attachedToAgent: response.attached_to_agent,
        agentId: response.agent_id || null,
      }));

      if (response.attached_to_agent) {
        toast.success("Document uploaded and attached to agent! Indexing started...");
      } else if (response.agent_attachment_error) {
        toast.warning(`Document uploaded but failed to attach to agent: ${response.agent_attachment_error}`);
      } else {
        toast.success("Document uploaded! Indexing started...");
      }

      // Start polling for indexing status
      if (response.indexing_status !== "succeeded") {
        pollAttemptsRef.current = 0;
        pollTimeoutRef.current = setTimeout(() => {
          pollIndexingStatus(response.document_id);
        }, POLL_INTERVAL_MS);
      } else {
        onSuccess?.();
      }
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to upload document";
      setState((prev) => ({
        ...prev,
        isUploading: false,
        uploadProgress: 0,
        error: errorMessage,
      }));
      toast.error(errorMessage);
    }
  };

  const handleClearFile = () => {
    setState((prev) => ({
      ...prev,
      file: null,
      error: null,
    }));
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const getStatusIcon = () => {
    if (state.indexingStatus === "succeeded") {
      return <CheckCircle2 className="h-8 w-8 text-green-500" />;
    }
    if (state.indexingStatus === "failed" || state.error) {
      return <AlertCircle className="h-8 w-8 text-destructive" />;
    }
    if (state.isUploading || state.indexingStatus === "processing" || state.indexingStatus === "created") {
      return <Loader2 className="h-8 w-8 text-primary animate-spin" />;
    }
    return <Upload className="h-8 w-8 text-muted-foreground" />;
  };

  const getStatusMessage = () => {
    if (state.indexingStatus === "succeeded") {
      return "Document indexed and ready for RAG!";
    }
    if (state.error) {
      return state.error;
    }
    if (state.isUploading) {
      return "Uploading document...";
    }
    if (state.indexingStatus === "processing" || state.indexingStatus === "created") {
      return `Indexing document... ${state.indexingProgress}%`;
    }
    return null;
  };

  const isProcessing =
    state.isUploading ||
    state.indexingStatus === "processing" ||
    state.indexingStatus === "created";

  const isComplete = state.indexingStatus === "succeeded";
  const hasError = !!state.error || state.indexingStatus === "failed";

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" />
            Upload Knowledge Base Document
          </DialogTitle>
          <DialogDescription>
            Upload a document to enhance your AI agent's knowledge with RAG (Retrieval-Augmented Generation).
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* File Selection Area */}
          {!state.documentId && (
            <div
              className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                state.file ? "border-primary bg-primary/5" : "border-muted-foreground/25 bg-muted/30"
              }`}
            >
              {getStatusIcon()}
              <div className="mt-4 space-y-2">
                <h3 className="text-lg font-semibold">
                  {state.file ? state.file.name : "Select a document"}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {state.file
                    ? `${(state.file.size / (1024 * 1024)).toFixed(2)} MB`
                    : `Supported: ${ALLOWED_FILE_TYPES.join(", ")} (max ${MAX_FILE_SIZE_MB}MB)`}
                </p>
              </div>

              <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_FILE_TYPES.join(",")}
                onChange={handleFileSelect}
                disabled={isProcessing}
                className="hidden"
                id="kb-file-upload"
              />

              <div className="mt-4 flex gap-2 justify-center">
                {!state.file ? (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isProcessing}
                  >
                    <Upload className="h-4 w-4 mr-2" />
                    Choose File
                  </Button>
                ) : (
                  <>
                    <Button
                      type="button"
                      variant="outline"
                      onClick={handleClearFile}
                      disabled={isProcessing}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Remove
                    </Button>
                    <Button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isProcessing}
                      variant="secondary"
                    >
                      Change File
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Progress Section */}
          {(isProcessing || isComplete || hasError) && state.documentId && (
            <div className="space-y-4">
              <div className="flex items-center gap-3">
                {getStatusIcon()}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{state.documentName}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">{getStatusMessage()}</p>
                </div>
              </div>

              {isProcessing && (
                <Progress
                  value={state.indexingStatus === "processing" ? state.indexingProgress : state.uploadProgress}
                  className="h-2"
                />
              )}

              {isComplete && (
                <div className="space-y-3">
                  <div className="bg-green-50 dark:bg-green-950/30 border border-green-200 dark:border-green-800 rounded-lg p-4">
                    <p className="text-sm text-green-700 dark:text-green-300">
                      ✓ Your document has been indexed and is now available for RAG queries.
                    </p>
                  </div>
                  
                  {state.attachedToAgent && (
                    <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-4 flex items-start gap-3">
                      <Bot className="h-5 w-5 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                          Attached to Agent
                        </p>
                        <p className="text-sm text-blue-600 dark:text-blue-400">
                          This document is now part of your AI agent's knowledge base.
                          The agent will use it to provide more accurate, context-aware responses.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {hasError && (
                <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
                  <p className="text-sm text-destructive">{state.error}</p>
                </div>
              )}
            </div>
          )}

          {/* Error Display (before upload) */}
          {state.error && !state.documentId && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <p className="text-sm text-destructive">{state.error}</p>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleClose} disabled={isProcessing}>
            {isComplete || hasError ? "Close" : "Cancel"}
          </Button>
          {!state.documentId && (
            <Button
              onClick={handleUpload}
              disabled={!state.file || isProcessing}
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4 mr-2" />
                  Upload & Index
                </>
              )}
            </Button>
          )}
          {isComplete && (
            <Button onClick={() => { resetState(); }}>
              Upload Another
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

function getStatusErrorMessage(status: RAGIndexingStatus): string {
  switch (status) {
    case "failed":
      return "Indexing failed. Please try again with a different document.";
    case "rag_limit_exceeded":
      return "RAG limit exceeded. Please upgrade your plan or remove some documents.";
    case "document_too_small":
      return "Document is too small to index. Please upload a larger document.";
    case "cannot_index_folder":
      return "Cannot index folders. Please upload individual files.";
    default:
      return "An error occurred during indexing.";
  }
}
