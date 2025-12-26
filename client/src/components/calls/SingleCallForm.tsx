import { Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface SingleCallFormProps {
  clientName: string;
  setClientName: (value: string) => void;
  phoneNumber: string;
  setPhoneNumber: (value: string) => void;
  email?: string;
  setEmail?: (value: string) => void;
  isSubmitting: boolean;
  errors: {
    clientName?: string;
    phoneNumber?: string;
    email?: string;
  };
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
}

export const SingleCallForm = ({
  clientName,
  setClientName,
  phoneNumber,
  setPhoneNumber,
  email,
  setEmail,
  isSubmitting,
  errors,
  onSubmit,
  onCancel,
}: SingleCallFormProps) => {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
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

      <div className="space-y-2">
        <Label htmlFor="email">Email Address</Label>
        <Input
          id="email"
          type="email"
          placeholder="email@example.com"
          value={email || ""}
          onChange={(e) => setEmail?.(e.target.value)}
          disabled={isSubmitting}
          className={errors.email ? "border-destructive" : ""}
        />
        {errors.email && (
          <p className="text-xs text-destructive">{errors.email}</p>
        )}
      </div>

      <div className="flex gap-2 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
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
  );
};
