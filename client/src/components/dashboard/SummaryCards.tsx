import { Phone, CheckCircle, TrendingUp } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatPercentage } from "@/utils/formatters";
import type { CallSummary } from "@/types/call.types";

interface SummaryCardsProps {
  summary: CallSummary | null;
  isLoading: boolean;
}

export const SummaryCards = ({ summary, isLoading }: SummaryCardsProps) => {
  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-8 w-16 mb-4" />
            <Skeleton className="h-2 w-full" />
          </Card>
        ))}
      </div>
    );
  }

  if (!summary) return null;

  const cards = [
    {
      title: "Total Calls",
      value: summary.total_calls,
      icon: Phone,
      gradient: "bg-gradient-primary",
      iconColor: "text-primary",
    },
    {
      title: "Conversions",
      value: summary.conversions,
      icon: CheckCircle,
      gradient: "bg-gradient-success",
      iconColor: "text-success",
    },
    {
      title: "Conversion Rate",
      value: formatPercentage(summary.conversion_rate),
      icon: TrendingUp,
      gradient: "bg-gradient-primary",
      iconColor: "text-accent",
      progress: summary.conversion_rate * 100,
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-3 animate-fade-in">
      {cards.map((card) => {
        const Icon = card.icon;
        return (
          <Card
            key={card.title}
            className="p-6 transition-all duration-300 hover:shadow-lg hover:-translate-y-1 bg-gradient-card border-border/50"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-muted-foreground">{card.title}</h3>
              <div className={`p-2 rounded-lg bg-${card.gradient}`}>
                <Icon className={`h-4 w-4 ${card.iconColor}`} />
              </div>
            </div>
            <div className="space-y-2">
              <p className="text-3xl font-bold text-foreground">{card.value}</p>
              {card.progress !== undefined && (
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full ${card.gradient} transition-all duration-500`}
                    style={{ width: `${card.progress}%` }}
                  />
                </div>
              )}
            </div>
          </Card>
        );
      })}
    </div>
  );
};
