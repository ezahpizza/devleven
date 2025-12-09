import { useState } from "react";
import { Eye, Copy, Calendar } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { formatDuration, formatRelativeTime, truncateCallId, getInitials } from "@/utils/formatters";
import { toast } from "sonner";
import type { CallRecord } from "@/types/call.types";
import { cn } from "@/lib/utils";

interface CallTableProps {
  calls: CallRecord[];
  isLoading: boolean;
  onViewDetails: (call: CallRecord) => void;
  highlightedCallId?: string | null;
}

const getSentimentEmoji = (sentiment: string) => {
  switch (sentiment) {
    case "positive":
      return "😊";
    case "neutral":
      return "😐";
    case "negative":
      return "😢";
    default:
      return "❓";
  }
};

const getSentimentVariant = (sentiment: string): "positive" | "neutral" | "negative" => {
  return sentiment as "positive" | "neutral" | "negative";
};

export const CallTable = ({ calls, isLoading, onViewDetails, highlightedCallId }: CallTableProps) => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyCallId = async (callId: string) => {
    try {
      await navigator.clipboard.writeText(callId);
      setCopiedId(callId);
      toast.success("Call ID copied to clipboard");
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      toast.error("Failed to copy Call ID");
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="p-4 border border-border rounded-lg">
            <div className="flex items-center gap-4">
              <Skeleton className="h-10 w-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
              <Skeleton className="h-8 w-20" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (calls.length === 0) {
    return (
      <div className="text-center py-12 border border-dashed border-border rounded-lg">
        <p className="text-muted-foreground">No calls found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {calls.map((call) => (
        <div
          key={call.call_id}
          className={cn(
            "p-4 border border-border rounded-lg transition-all duration-300 hover:shadow-md hover:border-primary/50 bg-card",
            highlightedCallId === call.call_id && "animate-highlight"
          )}
        >
          {/* Mobile & Desktop Layout */}
          <div className="flex flex-col md:flex-row md:items-center gap-4">
            {/* Avatar & Name */}
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <span className="text-sm font-semibold text-primary">
                  {getInitials(call.client_name)}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <h4 className="font-semibold text-foreground truncate">{call.client_name}</h4>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <button
                    onClick={() => handleCopyCallId(call.call_id)}
                    className="flex items-center gap-1 hover:text-foreground transition-colors"
                  >
                    <span className="truncate max-w-[120px]">{truncateCallId(call.call_id)}</span>
                    <Copy className={cn("h-3 w-3", copiedId === call.call_id && "text-success")} />
                  </button>
                  <span>•</span>
                  <span>{formatRelativeTime(call.timestamp)}</span>
                </div>
              </div>
            </div>

            {/* Metrics */}
            <div className="flex flex-wrap items-center gap-2 md:gap-4">
              <Badge variant={getSentimentVariant(call.insights.sentiment)}>
                {getSentimentEmoji(call.insights.sentiment)} {call.insights.sentiment}
              </Badge>
              
              <div className="text-sm text-muted-foreground">
                {formatDuration(call.insights.duration_sec)}
              </div>

              {call.insights.topics.length > 0 && (
                <div className="flex gap-1">
                  {call.insights.topics.slice(0, 2).map((topic) => (
                    <Badge key={topic} variant="secondary" className="text-xs">
                      {topic}
                    </Badge>
                  ))}
                  {call.insights.topics.length > 2 && (
                    <Badge variant="secondary" className="text-xs">
                      +{call.insights.topics.length - 2}
                    </Badge>
                  )}
                </div>
              )}

              {call.follow_up_date ? (
                <Badge variant="secondary" className="gap-1">
                  <Calendar className="h-3 w-3" />
                  {new Date(call.follow_up_date).toLocaleDateString()}
                </Badge>
              ) : (
                <Badge variant="outline" className="text-muted-foreground">
                  No follow-up
                </Badge>
              )}

              <Button
                size="sm"
                variant="outline"
                onClick={() => onViewDetails(call)}
                className="gap-2"
              >
                <Eye className="h-4 w-4" />
                <span className="hidden sm:inline">View</span>
              </Button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
