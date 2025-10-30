import { useState, useEffect, useCallback } from "react";
import { Phone, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { WebSocketIndicator } from "@/components/dashboard/WebSocketIndicator";
import { SummaryCards } from "@/components/dashboard/SummaryCards";
import { CallTable } from "@/components/dashboard/CallTable";
import { CallDetailModal } from "@/components/dashboard/CallDetailModal";
import { Pagination } from "@/components/dashboard/Pagination";
import { InitiateCallModal } from "@/components/calls/InitiateCallModal";
import { useWebSocket } from "@/hooks/useWebSocket";
import { callsApi } from "@/services/callsApi";
import { toast } from "sonner";
import type {
  CallRecord,
  CallSummary,
  WebSocketMessage,
  CallInProgressData,
} from "@/types/call.types";

const DEFAULT_PAGE = 1;
const DEFAULT_PAGE_SIZE = 20;

const Dashboard = () => {
  const [calls, setCalls] = useState<CallRecord[]>([]);
  const [summary, setSummary] = useState<CallSummary | null>(null);
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);
  const [isCallModalOpen, setIsCallModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(DEFAULT_PAGE);
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE);
  const [totalItems, setTotalItems] = useState(0);
  const [highlightedCallId, setHighlightedCallId] = useState<string | null>(null);

  const fetchCalls = useCallback(async (page: number, size: number) => {
    try {
      setIsLoading(true);
      const response = await callsApi.getCalls(page, size);
      setCalls(response.items);
      setTotalItems(response.total);
      setCurrentPage(response.page);
      setPageSize(response.page_size);
    } catch (error) {
      toast.error("Failed to fetch calls");
      console.error("Error fetching calls:", error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchSummary = useCallback(async () => {
    try {
      const data = await callsApi.getSummary();
      setSummary(data);
    } catch (error) {
      console.error("Error fetching summary:", error);
    }
  }, []);

  const handleWebSocketMessage = useCallback(
    (message: WebSocketMessage) => {
      console.log("WebSocket message received:", message);

      if (message.event === "call_in_progress") {
        const data = message.data as CallInProgressData;
        toast.info(`Call in progress: ${data.client_name}`, {
          description: `Call SID: ${data.call_sid}`,
        });
      } else if (message.event === "call_completed") {
        const newCall = message.data as CallRecord;

        // Add the new call to the top of the list
        setCalls((prev) => {
          const filtered = prev.filter((call) => call.call_id !== newCall.call_id);
          return [newCall, ...filtered];
        });

        // Highlight the new call
        setHighlightedCallId(newCall.call_id);
        setTimeout(() => setHighlightedCallId(null), 3000);

        // Refresh summary
        fetchSummary();

        toast.success(`Call completed: ${newCall.client_name}`, {
          description: newCall.conversion_status ? "✓ Converted" : "No conversion",
        });
      }
    },
    [fetchSummary]
  );

  const { isConnected } = useWebSocket("/ws/dashboard", {
    onMessage: handleWebSocketMessage,
  });

  useEffect(() => {
    fetchCalls(DEFAULT_PAGE, DEFAULT_PAGE_SIZE);
    fetchSummary();
  }, [fetchCalls, fetchSummary]);

  const handleRefresh = useCallback(() => {
    fetchCalls(currentPage, pageSize);
    fetchSummary();
    toast.success("Dashboard refreshed");
  }, [fetchCalls, fetchSummary, currentPage, pageSize]);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    fetchCalls(newPage, pageSize);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handlePageSizeChange = (newSize: number) => {
    setPageSize(newSize);
    setCurrentPage(DEFAULT_PAGE);
    fetchCalls(DEFAULT_PAGE, newSize);
  };

  const totalPages = Math.ceil(totalItems / pageSize);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-gradient-primary flex items-center justify-center">
                <Phone className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-foreground">Voice Agent Dashboard</h1>
                <p className="text-sm text-muted-foreground">Monitor and manage your calls</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <WebSocketIndicator isConnected={isConnected} />
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
                className="gap-2"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} />
                <span className="hidden sm:inline">Refresh</span>
              </Button>
              <Button
                size="sm"
                onClick={() => setIsCallModalOpen(true)}
                className="gap-2"
              >
                <Phone className="h-4 w-4" />
                New Call
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 space-y-8">
        {/* Summary Cards */}
        <SummaryCards summary={summary} isLoading={isLoading && !summary} />

        {/* Call List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">Recent Calls</h2>
            {!isLoading && (
              <p className="text-sm text-muted-foreground">
                {totalItems} total calls
              </p>
            )}
          </div>
          
          <CallTable
            calls={calls}
            isLoading={isLoading}
            onViewDetails={setSelectedCall}
            highlightedCallId={highlightedCallId}
          />

          {!isLoading && totalPages > 1 && (
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              pageSize={pageSize}
              totalItems={totalItems}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
          )}
        </div>
      </main>

      {/* Modals */}
      <CallDetailModal
        call={selectedCall}
        isOpen={!!selectedCall}
        onClose={() => setSelectedCall(null)}
      />

      <InitiateCallModal
        isOpen={isCallModalOpen}
        onClose={() => setIsCallModalOpen(false)}
        onSuccess={() => {
          fetchCalls(currentPage, pageSize);
          fetchSummary();
        }}
      />
    </div>
  );
};

export default Dashboard;
