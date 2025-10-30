import { cn } from "@/lib/utils";

interface WebSocketIndicatorProps {
  isConnected: boolean;
  className?: string;
}

export const WebSocketIndicator = ({ isConnected, className }: WebSocketIndicatorProps) => {
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="relative flex items-center">
        <div
          className={cn(
            "h-2 w-2 rounded-full transition-colors",
            isConnected ? "bg-success" : "bg-destructive"
          )}
        />
        {isConnected && (
          <div className="absolute h-2 w-2 rounded-full bg-success animate-pulse-glow" />
        )}
      </div>
      <span className="text-sm font-medium text-muted-foreground">
        {isConnected ? "Live" : "Offline"}
      </span>
    </div>
  );
};
