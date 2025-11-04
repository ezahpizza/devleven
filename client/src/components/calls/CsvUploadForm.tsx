import { useRef } from "react";
import { Upload, FileText, X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface CsvUploadFormProps {
  csvFile: File | null;
  csvError: string;
  isSubmitting: boolean;
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onSubmit: (e: React.FormEvent) => void;
  onCancel: () => void;
  onClearFile: () => void;
}

export const CsvUploadForm = ({
  csvFile,
  csvError,
  isSubmitting,
  onFileSelect,
  onSubmit,
  onCancel,
  onClearFile,
}: CsvUploadFormProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleClearFile = () => {
    onClearFile();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="space-y-4">
        <div className="border-2 border-dashed rounded-lg p-8 text-center bg-muted/30">
          <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
          <div className="space-y-2">
            <h3 className="text-lg font-semibold">Upload CSV File</h3>
            <p className="text-sm text-muted-foreground">
              Calls will be initiated in batches of 5 at a time
            </p>
          </div>
          
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={onFileSelect}
            disabled={isSubmitting}
            className="hidden"
            id="csv-upload"
          />
          
          <Button
            type="button"
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            disabled={isSubmitting}
            className="mt-4"
          >
            <FileText className="h-4 w-4 mr-2" />
            Select CSV File
          </Button>
          
          {csvFile && (
            <div className="mt-4 p-3 bg-background rounded-md border">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">{csvFile.name}</span>
                  <span className="text-xs text-muted-foreground">
                    ({(csvFile.size / 1024).toFixed(1)} KB)
                  </span>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleClearFile}
                  disabled={isSubmitting}
                  className="h-6 w-6 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
          
          {csvError && (
            <p className="text-xs text-destructive mt-2">{csvError}</p>
          )}
        </div>

        <CsvFormatRequirements />
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
          disabled={isSubmitting || !csvFile}
          className="flex-1 gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="h-4 w-4 border-2 border-background border-t-transparent rounded-full animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              Upload & Initiate Calls
            </>
          )}
        </Button>
      </div>
    </form>
  );
};

const CsvFormatRequirements = () => (
  <div className="space-y-2 p-4 bg-muted/50 rounded-lg">
    <h4 className="text-sm font-semibold flex items-center gap-2">
      <FileText className="h-4 w-4" />
      CSV Format Requirements
    </h4>
    <ul className="text-xs text-muted-foreground space-y-1 list-disc list-inside">
      <li>CSV must have headers in the first row</li>
      <li>Required columns: <code className="bg-background px-1 py-0.5 rounded">name</code> or <code className="bg-background px-1 py-0.5 rounded">client_name</code></li>
      <li>Required columns: <code className="bg-background px-1 py-0.5 rounded">phone</code> or <code className="bg-background px-1 py-0.5 rounded">number</code></li>
      <li>Phone numbers should be in E.164 format (e.g., +14155552671)</li>
      <li>Maximum file size: 5MB</li>
      <li>Calls will be processed in batches of 5 concurrently</li>
    </ul>
  </div>
);
