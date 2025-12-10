export interface CallInsights {
  topics: string[];
  duration_sec: number;
}

export interface NotificationPreferences {
  notify_email: boolean;
  notify_whatsapp: boolean;
  email_address: string | null;
  whatsapp_number: string | null;
  email_sent: boolean;
  whatsapp_sent: boolean;
}

export interface CallRecord {
  call_id: string;
  client_name: string;
  transcript: string;
  insights: CallInsights;
  conversion_status: boolean;
  timestamp: string;
  summary: string | null;
  follow_up_date: string | null;
  notification_preferences: NotificationPreferences | null;
  phone_number: string | null;
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
