import React from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowUpCircle, ArrowDownCircle, MinusCircle, AlertTriangle } from 'lucide-react';
import { ExecutiveSummary as ExecutiveSummaryType } from '@shared/schema';

interface ExecutiveSummaryProps {
  summary: ExecutiveSummaryType;
}

export const ExecutiveSummary: React.FC<ExecutiveSummaryProps> = ({ summary }) => {
  const getTrendIcon = (direction: string) => {
    switch (direction?.toLowerCase()) {
      case 'bullish':
        return <ArrowUpCircle className="h-5 w-5 text-green-500" />;
      case 'bearish':
        return <ArrowDownCircle className="h-5 w-5 text-red-500" />;
      case 'neutral':
        return <MinusCircle className="h-5 w-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'negative':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      case 'neutral':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  const getActionColor = (action: string) => {
    switch (action?.toLowerCase()) {
      case 'buy':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'sell':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      case 'hold':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Executive Summary</CardTitle>
        <CardDescription>Market analysis and trading recommendation</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Market Overview */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Market Overview</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-center space-x-2">
                {getTrendIcon(summary.market_overview.market_trend.direction)}
                <div>
                  <p className="text-sm font-medium">
                    {summary.market_overview.market_trend.direction} Trend
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {summary.market_overview.market_trend.timeframe}
                  </p>
                </div>
              </div>
              <div>
                <Badge className={getSentimentColor(summary.market_overview.sentiment)}>
                  {summary.market_overview.sentiment} Sentiment
                </Badge>
              </div>
            </div>
            <div className="mt-2 grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Support</p>
                <p className="font-medium">${summary.market_overview.key_levels.nearest_support}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Resistance</p>
                <p className="font-medium">${summary.market_overview.key_levels.nearest_resistance}</p>
              </div>
            </div>
          </div>

          <Separator />

          {/* Trading Recommendation */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Trading Recommendation</h3>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Badge className={getActionColor(summary.trading_recommendation.action)}>
                  {summary.trading_recommendation.action.toUpperCase()}
                </Badge>
                <span className="text-sm">
                  {summary.trading_recommendation.confidence}% Confidence
                </span>
              </div>
              <div className="space-y-1">
                {summary.trading_recommendation.key_reasons.map((reason, index) => (
                  <p key={index} className="text-sm text-muted-foreground">
                    • {reason}
                  </p>
                ))}
              </div>
              <div className="grid grid-cols-2 gap-4 mt-2">
                <div>
                  <p className="text-sm text-muted-foreground">Stop Loss</p>
                  <p className="font-medium">${summary.trading_recommendation.risk_profile.stop_loss}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Take Profit</p>
                  <p className="font-medium">${summary.trading_recommendation.risk_profile.take_profit}</p>
                </div>
              </div>
            </div>
          </div>

          <Separator />

          {/* Key Metrics */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Meeting Metrics</h3>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{summary.key_metrics.participants}</p>
                <p className="text-sm text-muted-foreground">Participants</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{summary.key_metrics.analysis_points}</p>
                <p className="text-sm text-muted-foreground">Analyses</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{summary.key_metrics.decisions_made}</p>
                <p className="text-sm text-muted-foreground">Decisions</p>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};