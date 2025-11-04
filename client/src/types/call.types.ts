export interface CallInsights {
  sentiment: "positive" | "neutral" | "negative";
  topics: string[];
  duration_sec: number;
}

export interface CallRecord {
  call_id: string;
  client_name: string;
  transcript: string;
  insights: CallInsights;
  conversion_status: boolean;
  timestamp: string;
}

export interface PaginatedCallResponse {
  page: number;
  page_size: number;
  total: number;
  items: CallRecord[];
}

export interface CallSummary {
  total_calls: number;
  conversions: number;
  conversion_rate: number;
}

export interface OutboundCallRequest {
  number: string;
  client_name: string;
}

export interface OutboundCallResponse {
  success: boolean;
  message: string;
  callSid: string;
  clientName: string;
  phoneNumber: string;
}

export interface CallRecipient {
  number: string;
  client_name: string;
}

export interface BulkOutboundCallRequest {
  recipients: CallRecipient[];
}

export interface CallResult {
  success: boolean;
  call_sid: string | null;
  client_name: string;
  phone_number: string;
  error?: string;
}

export interface BulkOutboundCallResponse {
  total_requested: number;
  successful: number;
  failed: number;
  results: CallResult[];
}

export interface WebSocketMessage {
  event: "call_in_progress" | "call_completed";
  data: CallInProgressData | CallRecord;
}

export interface CallInProgressData {
  call_sid: string;
  client_name: string;
  phone_number: string;
  status: string;
}
