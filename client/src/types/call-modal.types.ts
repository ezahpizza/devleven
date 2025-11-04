export interface RecipientError {
  clientName?: string;
  phoneNumber?: string;
}

export interface ApiError {
  response?: {
    data?: {
      detail?: string;
      error?: string;
    };
  };
}

export interface CallFormErrors {
  clientName?: string;
  phoneNumber?: string;
}
