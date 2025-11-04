import api from "./api";
import type {
  PaginatedCallResponse,
  CallSummary,
  CallRecord,
  OutboundCallRequest,
  OutboundCallResponse,
  BulkOutboundCallRequest,
  BulkOutboundCallResponse,
} from "@/types/call.types";

export const callsApi = {
  // Fetch paginated call records
  getCalls: async (page: number = 1, pageSize: number = 20): Promise<PaginatedCallResponse> => {
    const response = await api.get<PaginatedCallResponse>("/api/calls", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  // Get call analytics summary
  getSummary: async (): Promise<CallSummary> => {
    const response = await api.get<CallSummary>("/api/calls/summary");
    return response.data;
  },

  // Get single call record by ID
  getCallById: async (callId: string): Promise<CallRecord> => {
    const response = await api.get<CallRecord>(`/api/call/${callId}`);
    return response.data;
  },

  // Initiate outbound call
  initiateCall: async (data: OutboundCallRequest): Promise<OutboundCallResponse> => {
    const response = await api.post<OutboundCallResponse>("/api/initiate_call", data);
    return response.data;
  },

  // Initiate bulk outbound calls
  initiateBulkCalls: async (data: BulkOutboundCallRequest): Promise<BulkOutboundCallResponse> => {
    const response = await api.post<BulkOutboundCallResponse>("/api/outbound-calls/bulk", data);
    return response.data;
  },

  // Initiate bulk calls from CSV file
  initiateBulkCallsFromCSV: async (file: File): Promise<BulkOutboundCallResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    
    const response = await api.post<BulkOutboundCallResponse>("/api/outbound-calls/bulk-csv", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },
};
