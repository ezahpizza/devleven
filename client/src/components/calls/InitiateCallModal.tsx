import { useState } from "react";
import { Phone, Users, Upload } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useSingleCall, useBulkCalls, useCsvUpload } from "@/hooks/useCallForms";
import { SingleCallForm } from "./SingleCallForm";
import { BulkCallForm } from "./BulkCallForm";
import { CsvUploadForm } from "./CsvUploadForm";

interface InitiateCallModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const InitiateCallModal = ({ isOpen, onClose, onSuccess }: InitiateCallModalProps) => {
  const [activeTab, setActiveTab] = useState<"single" | "bulk" | "csv">("single");

  // Handlers for success and close
  const handleSuccess = () => {
    onSuccess?.();
    onClose();
  };

  // Initialize hooks
  const singleCall = useSingleCall(handleSuccess);
  const bulkCalls = useBulkCalls(handleSuccess);
  const csvUpload = useCsvUpload(handleSuccess);

  const handleClose = () => {
    if (!singleCall.isSubmitting && !bulkCalls.isSubmitting && !csvUpload.isSubmitting) {
      singleCall.reset();
      bulkCalls.reset();
      csvUpload.reset();
      setActiveTab("single");
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <Phone className="h-5 w-5 text-primary" />
              Initiate Outbound Call
            </DialogTitle>
          </div>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "single" | "bulk" | "csv")} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="single" className="gap-2">
              <Phone className="h-4 w-4" />
              Single Call
            </TabsTrigger>
            <TabsTrigger value="bulk" className="gap-2">
              <Users className="h-4 w-4" />
              Bulk Calls
            </TabsTrigger>
            <TabsTrigger value="csv" className="gap-2">
              <Upload className="h-4 w-4" />
              CSV Upload
            </TabsTrigger>
          </TabsList>

          <TabsContent value="single" className="mt-4">
            <SingleCallForm
              clientName={singleCall.clientName}
              setClientName={singleCall.setClientName}
              phoneNumber={singleCall.phoneNumber}
              setPhoneNumber={singleCall.setPhoneNumber}
              isSubmitting={singleCall.isSubmitting}
              errors={singleCall.errors}
              onSubmit={singleCall.handleSubmit}
              onCancel={handleClose}
            />
          </TabsContent>

          <TabsContent value="bulk" className="mt-4">
            <BulkCallForm
              recipients={bulkCalls.recipients}
              recipientErrors={bulkCalls.recipientErrors}
              isSubmitting={bulkCalls.isSubmitting}
              onSubmit={bulkCalls.handleSubmit}
              onCancel={handleClose}
              onAddRecipient={bulkCalls.addRecipient}
              onRemoveRecipient={bulkCalls.removeRecipient}
              onUpdateRecipient={bulkCalls.updateRecipient}
            />
          </TabsContent>

          <TabsContent value="csv" className="mt-4">
            <CsvUploadForm
              csvFile={csvUpload.csvFile}
              csvError={csvUpload.csvError}
              isSubmitting={csvUpload.isSubmitting}
              onFileSelect={csvUpload.handleFileSelect}
              onSubmit={csvUpload.handleSubmit}
              onCancel={handleClose}
              onClearFile={csvUpload.clearFile}
            />
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
