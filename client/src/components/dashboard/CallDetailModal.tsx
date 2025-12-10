import { Phone, Clock, MessageSquare, Calendar, Sparkles, Mail, MessageCircle, CheckCircle, XCircle } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDuration, formatRelativeTime, formatDate } from "@/utils/formatters";
import type { CallRecord } from "@/types/call.types";

interface CallDetailModalProps {
  call: CallRecord | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CallDetailModal = ({ call, isOpen, onClose }: CallDetailModalProps) => {
  if (!call) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[90vh] p-0 gap-0">
        <DialogHeader className="px-6 py-4 border-b border-border">
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-2xl">{call.client_name}</DialogTitle>
              <div className="flex items-center gap-2 mt-1">
                <p className="text-sm text-muted-foreground">
                  Call ID: {call.call_id}
                </p>
                {call.phone_number && (
                  <p className="text-sm text-muted-foreground">
                    • {call.phone_number}
                  </p>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        <ScrollArea className="flex-1 px-6 py-4 max-h-[calc(90vh-120px)]">
          {/* Metadata Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Duration</p>
                <p className="text-sm font-semibold">{formatDuration(call.insights.duration_sec)}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Follow-up</p>
                <p className="text-sm font-semibold">
                  {call.follow_up_date 
                    ? formatDate(call.follow_up_date) 
                    : "Not scheduled"}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="text-xs text-muted-foreground">Time</p>
                <p className="text-sm font-semibold">{formatRelativeTime(call.timestamp)}</p>
              </div>
            </div>
          </div>

          {/* Notification Status */}
          {call.notification_preferences && (call.notification_preferences.notify_email || call.notification_preferences.notify_whatsapp) && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <MessageCircle className="h-4 w-4" />
                Notification Status
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {call.notification_preferences.notify_email && (
                  <div className="flex items-center gap-3 bg-muted/50 rounded-lg p-3">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">Email</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {call.notification_preferences.email_address || "No address"}
                      </p>
                    </div>
                    {call.notification_preferences.email_sent ? (
                      <CheckCircle className="h-4 w-4 text-success" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                )}
                {call.notification_preferences.notify_whatsapp && (
                  <div className="flex items-center gap-3 bg-muted/50 rounded-lg p-3">
                    <MessageCircle className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1">
                      <p className="text-sm font-medium">WhatsApp</p>
                      <p className="text-xs text-muted-foreground truncate">
                        {call.notification_preferences.whatsapp_number || "No number"}
                      </p>
                    </div>
                    {call.notification_preferences.whatsapp_sent ? (
                      <CheckCircle className="h-4 w-4 text-success" />
                    ) : (
                      <XCircle className="h-4 w-4 text-muted-foreground" />
                    )}
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Summary */}
          {call.summary && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-primary" />
                AI Summary
              </h3>
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-4">
                <p className="text-sm text-foreground leading-relaxed">{call.summary}</p>
              </div>
            </div>
          )}

          {/* Topics */}
          {call.insights.topics.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Topics Discussed
              </h3>
              <div className="flex flex-wrap gap-2">
                {call.insights.topics.map((topic) => (
                  <Badge key={topic} variant="secondary">
                    {topic}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Transcript */}
          <div>
            <h3 className="text-sm font-semibold mb-3">Full Transcript</h3>
            <div className="bg-muted/50 rounded-lg p-4 space-y-3">
              {call.transcript.split("\n").map((line, index) => {
                const isAgent = line.toLowerCase().startsWith("agent:");
                const isCustomer = line.toLowerCase().startsWith("customer:");
                
                return (
                  <div
                    key={index}
                    className={`text-sm leading-relaxed ${
                      isAgent ? "text-primary font-medium" : 
                      isCustomer ? "text-foreground" : 
                      "text-muted-foreground"
                    }`}
                  >
                    {line}
                  </div>
                );
              })}
            </div>
          </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};
