import { useState } from "react";
import { toast } from "sonner";
import { callsApi } from "@/services/callsApi";
import { isValidPhoneNumber, isValidClientName, sanitizePhoneNumber } from "@/utils/validators";
import type { CallRecipient, BulkOutboundCallResponse } from "@/types/call.types";
import type { CallFormErrors, RecipientError, ApiError } from "@/types/call-modal.types";

export const useSingleCall = (onSuccess?: () => void) => {
  const [clientName, setClientName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [email, setEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<CallFormErrors>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setErrors({});
    
    const newErrors: CallFormErrors = {};
    
    if (!isValidClientName(clientName)) {
      newErrors.clientName = "Client name must be between 2 and 255 characters";
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }
    
    const sanitizedPhone = sanitizePhoneNumber(phoneNumber);
    if (!isValidPhoneNumber(sanitizedPhone)) {
      newErrors.phoneNumber = "Please enter a valid phone number in E.164 format (e.g., +14155552671)";
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await callsApi.initiateCall({
        client_name: clientName.trim(),
        number: sanitizedPhone,
        email: email?.trim() || undefined,
      });
      
      toast.success(`Call initiated to ${response.clientName}`, {
        description: `Call SID: ${response.callSid}`,
      });
      
      reset();
      onSuccess?.();
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const errorMessage = apiError.response?.data?.detail || "Failed to initiate call";
      toast.error("Error", {
        description: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const reset = () => {
    setClientName("");
    setPhoneNumber("");
    setEmail("");
    setErrors({});
  };

  return {
    clientName,
    setClientName,
    phoneNumber,
    setPhoneNumber,
    email,
    setEmail,
    isSubmitting,
    errors,
    handleSubmit,
    reset,
  };
};

export const useBulkCalls = (onSuccess?: () => void) => {
  const [recipients, setRecipients] = useState<CallRecipient[]>([
    { client_name: "", number: "", email: undefined }
  ]);
  const [recipientErrors, setRecipientErrors] = useState<RecipientError[]>([{}]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    setRecipientErrors(recipients.map(() => ({})));
    
    const newErrors: RecipientError[] = [];
    let hasErrors = false;
    const validRecipients: CallRecipient[] = [];
    
    recipients.forEach((recipient) => {
      const recipientError: RecipientError = {};
      
      if (!isValidClientName(recipient.client_name)) {
        recipientError.clientName = "Client name must be between 2 and 255 characters";
        hasErrors = true;
      }
      
      const sanitizedPhone = sanitizePhoneNumber(recipient.number);
      if (!isValidPhoneNumber(sanitizedPhone)) {
        recipientError.phoneNumber = "Please enter a valid phone number in E.164 format";
        hasErrors = true;
      } else {
        validRecipients.push({
          client_name: recipient.client_name.trim(),
          number: sanitizedPhone,
          email: recipient.email?.trim() || undefined
        });
      }
      if (recipient.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(recipient.email)) {
        recipientError.email = "Please enter a valid email address";
        hasErrors = true;
      }
      
      newErrors.push(recipientError);
    });
    
    if (hasErrors) {
      setRecipientErrors(newErrors);
      return;
    }
    
    setIsSubmitting(true);
    try {
      const response = await callsApi.initiateBulkCalls({
        recipients: validRecipients,
      });
      
      showBulkResults(response);
      reset();
      onSuccess?.();
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const errorMessage = apiError.response?.data?.error || "Failed to initiate bulk calls";
      toast.error("Error", {
        description: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const addRecipient = () => {
    setRecipients([...recipients, { client_name: "", number: "", email: undefined }]);
    setRecipientErrors([...recipientErrors, {}]);
  };

  const removeRecipient = (index: number) => {
    if (recipients.length > 1) {
      setRecipients(recipients.filter((_, i) => i !== index));
      setRecipientErrors(recipientErrors.filter((_, i) => i !== index));
    }
  };

  const updateRecipient = (index: number, field: keyof CallRecipient, value: string) => {
    const updated = [...recipients];
    updated[index][field] = value;
    setRecipients(updated);
  };

  const reset = () => {
    setRecipients([{ client_name: "", number: "" }]);
    setRecipientErrors([{}]);
  };

  return {
    recipients,
    recipientErrors,
    isSubmitting,
    handleSubmit,
    addRecipient,
    removeRecipient,
    updateRecipient,
    reset,
  };
};

export const useCsvUpload = (onSuccess?: () => void) => {
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [csvError, setCsvError] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      setCsvError("Please select a CSV file");
      setCsvFile(null);
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setCsvError("File size must be less than 5MB");
      setCsvFile(null);
      return;
    }

    setCsvError("");
    setCsvFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!csvFile) {
      setCsvError("Please select a CSV file");
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await callsApi.initiateBulkCallsFromCSV(csvFile);

      toast.success(`CSV bulk calls initiated`, {
        description: `${response.successful} successful, ${response.failed} failed out of ${response.total_requested} total. Calls processed in batches of 5.`,
      });

      showBulkResults(response);
      reset();
      onSuccess?.();
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const errorMessage = apiError.response?.data?.detail || "Failed to process CSV file";
      toast.error("Error", {
        description: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const reset = () => {
    setCsvFile(null);
    setCsvError("");
  };

  const clearFile = () => {
    setCsvFile(null);
  };

  return {
    csvFile,
    setCsvFile,
    csvError,
    isSubmitting,
    handleFileSelect,
    handleSubmit,
    reset,
    clearFile,
  };
};

// Helper function to show bulk call results
function showBulkResults(response: BulkOutboundCallResponse) {
  if (response.failed > 0) {
    const failedCalls = response.results.filter(r => !r.success);
    const failedCount = Math.min(failedCalls.length, 3);
    failedCalls.slice(0, failedCount).forEach(call => {
      toast.error(`Failed: ${call.client_name}`, {
        description: call.error || "Unknown error",
      });
    });
    if (failedCalls.length > 3) {
      toast.error(`...and ${failedCalls.length - 3} more failures`);
    }
  }
}
