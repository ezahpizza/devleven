import { useState } from "react";
import { Phone, X } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { callsApi } from "@/services/callsApi";
import { isValidPhoneNumber, isValidClientName, sanitizePhoneNumber } from "@/utils/validators";
import { toast } from "sonner";

interface InitiateCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const InitiateCallModal = ({ isOpen, onClose, onSuccess }: InitiateCallModalProps) => {
  const [clientName, setClientName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ clientName?: string; phoneNumber?: string }>({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Reset errors
    setErrors({});
    
    // Validate
    const newErrors: { clientName?: string; phoneNumber?: string } = {};
    
    if (!isValidClientName(clientName)) {
      newErrors.clientName = "Client name must be between 2 and 255 characters";
    }
    
    const sanitizedPhone = sanitizePhoneNumber(phoneNumber);
    if (!isValidPhoneNumber(sanitizedPhone)) {
      newErrors.phoneNumber = "Please enter a valid phone number in E.164 format (e.g., +14155552671)";
    }
    
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    // Submit
    setIsSubmitting(true);
    try {
      const response = await callsApi.initiateCall({
        client_name: clientName.trim(),
        number: sanitizedPhone,
      });
      
      toast.success(`Call initiated to ${response.clientName}`, {
        description: `Call SID: ${response.callSid}`,
      });
      
      // Reset form
      setClientName("");
      setPhoneNumber("");
      
      onSuccess?.();
      onClose();
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || "Failed to initiate call";
      toast.error("Error", {
        description: errorMessage,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setClientName("");
      setPhoneNumber("");
      setErrors({});
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5 text-primary" />
              Initiate New Call
            </DialogTitle>
          </div>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 pt-4">
          <div className="space-y-2">
            <Label htmlFor="clientName">Client Name</Label>
            <Input
              id="clientName"
              type="text"
              placeholder="Enter client name..."
              value={clientName}
              onChange={(e) => setClientName(e.target.value)}
              disabled={isSubmitting}
              className={errors.clientName ? "border-destructive" : ""}
            />
            {errors.clientName && (
              <p className="text-xs text-destructive">{errors.clientName}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="phoneNumber">Phone Number</Label>
            <Input
              id="phoneNumber"
              type="tel"
              placeholder="+14155552671"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              disabled={isSubmitting}
              className={errors.phoneNumber ? "border-destructive" : ""}
            />
            <p className="text-xs text-muted-foreground">
              Format: E.164 (e.g., +14155552671)
            </p>
            {errors.phoneNumber && (
              <p className="text-xs text-destructive">{errors.phoneNumber}</p>
            )}
          </div>

          <div className="flex gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isSubmitting}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="h-4 w-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
                  Calling...
                </>
              ) : (
                <>
                  <Phone className="h-4 w-4" />
                  Initiate Call
                </>
              )}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
};
