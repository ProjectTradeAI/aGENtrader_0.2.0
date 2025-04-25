import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useQuery } from '@tanstack/react-query';

interface AgentMessage {
  timestamp: string;
  agent: string;
  content: string;
  executiveSummary?: {
    market_overview?: {
      market_trend: {
        direction: string;
        timeframe: string;
      };
      key_indicators: Record<string, any>;
      sentiment: string;
    };
    trading_recommendation?: {
      action: string;
      confidence: number;
      key_reasons: string[];
      risk_profile: Record<string, any>;
    };
  };
}

export default function AgentActivity() {
  // Reduce polling frequency and add longer stale time
  const { data: messages, isLoading, error } = useQuery({
    queryKey: ['/api/logs/agent-messages'],
    refetchInterval: 60000, // Poll every minute instead of 30 seconds
    staleTime: 30000, // Consider data fresh for 30 seconds
    retry: 1, // Only retry once on failure
    retryDelay: 5000, // Wait 5 seconds before retrying
  });

  if (isLoading) {
    return (
      <Card className="min-h-[200px]">
        <CardHeader>
          <CardTitle>Agent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <p className="text-muted-foreground">Loading agent messages...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="min-h-[200px]">
        <CardHeader>
          <CardTitle>Agent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <p className="text-red-500">Error loading agent messages</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const sortedMessages = messages?.sort((a: AgentMessage, b: AgentMessage) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  ) || [];

  return (
    <Card className="min-h-[200px]">
      <CardHeader>
        <CardTitle>Agent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        {sortedMessages.length > 0 ? (
          <div className="space-y-4">
            {sortedMessages.map((msg: AgentMessage, idx: number) => (
              <div key={idx} className="border-b pb-4">
                <p className="font-medium">{msg.agent}</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(msg.timestamp).toLocaleString()}
                </p>
                {msg.executiveSummary ? (
                  <div className="mt-2 space-y-2">
                    {msg.executiveSummary.market_overview && (
                      <div className="bg-secondary/50 p-3 rounded-md">
                        <p className="font-medium">Market Overview</p>
                        <p>Trend: {msg.executiveSummary.market_overview.market_trend.direction} 
                          ({msg.executiveSummary.market_overview.market_trend.timeframe})</p>
                        <p>Sentiment: {msg.executiveSummary.market_overview.sentiment}</p>
                      </div>
                    )}
                    {msg.executiveSummary.trading_recommendation && (
                      <div className="bg-secondary/50 p-3 rounded-md">
                        <p className="font-medium">Trading Recommendation</p>
                        <p>Action: {msg.executiveSummary.trading_recommendation.action} 
                          ({msg.executiveSummary.trading_recommendation.confidence}% confidence)</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="mt-2">{msg.content}</p>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="flex items-center justify-center h-32">
            <p className="text-muted-foreground">No recent agent messages</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}