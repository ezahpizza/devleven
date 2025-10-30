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
