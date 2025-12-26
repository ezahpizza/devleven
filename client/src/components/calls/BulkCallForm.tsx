import { Plus, Trash2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { CallRecipient } from "@/types/call.types";
import type { RecipientError } from "@/types/call-modal.types";

interface BulkCallFormProps {
  recipients: CallRecipient[];
  recipientErrors: RecipientError[];
  isSubmitting: boolean;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  onAddRecipient: () => void;
  onRemoveRecipient: (index: number) => void;
  onUpdateRecipient: (index: number, field: keyof CallRecipient, value: string) => void;
}

export const BulkCallForm = ({
  recipients,
  recipientErrors,
  isSubmitting,
  onSubmit,
  onCancel,
  onAddRecipient,
  onRemoveRecipient,
  onUpdateRecipient,
}: BulkCallFormProps) => {
  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
        {recipients.map((recipient, index) => (
          <div key={index} className="p-4 border rounded-lg space-y-3 bg-muted/30">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Recipient {index + 1}</span>
              {recipients.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemoveRecipient(index)}
                  disabled={isSubmitting}
                  className="h-6 w-6 p-0 text-destructive hover:text-destructive"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor={`clientName-${index}`}>Client Name</Label>
              <Input
                id={`clientName-${index}`}
                type="text"
                placeholder="Enter client name..."
                value={recipient.client_name}
                onChange={(e) => onUpdateRecipient(index, "client_name", e.target.value)}
                disabled={isSubmitting}
                className={recipientErrors[index]?.clientName ? "border-destructive" : ""}
              />
              {recipientErrors[index]?.clientName && (
                <p className="text-xs text-destructive">{recipientErrors[index].clientName}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor={`phoneNumber-${index}`}>Phone Number</Label>
              <Input
                id={`phoneNumber-${index}`}
                type="tel"
                placeholder="+14155552671"
                value={recipient.number}
                onChange={(e) => onUpdateRecipient(index, "number", e.target.value)}
                disabled={isSubmitting}
                className={recipientErrors[index]?.phoneNumber ? "border-destructive" : ""}
              />
              {recipientErrors[index]?.phoneNumber && (
                <p className="text-xs text-destructive">{recipientErrors[index].phoneNumber}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor={`email-${index}`}>Email Address</Label>
              <Input
                id={`email-${index}`}
                type="email"
                placeholder="email@example.com"
                value={(recipient as any).email || ""}
                onChange={(e) => onUpdateRecipient(index, "email" as any, e.target.value)}
                disabled={isSubmitting}
                className={recipientErrors[index]?.email ? "border-destructive" : ""}
              />
              {recipientErrors[index]?.email && (
                <p className="text-xs text-destructive">{recipientErrors[index].email}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      <Button
        type="button"
        variant="outline"
        onClick={onAddRecipient}
        disabled={isSubmitting || recipients.length >= 50}
        className="w-full gap-2"
      >
        <Plus className="h-4 w-4" />
        Add Recipient {recipients.length >= 50 && "(Max 50)"}
      </Button>

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
              <Users className="h-4 w-4" />
              Initiate {recipients.length} Call{recipients.length !== 1 ? 's' : ''}
            </>
          )}
        </Button>
      </div>
    </form>
  );
};
