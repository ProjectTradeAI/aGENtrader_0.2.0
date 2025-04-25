import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Loader2, RefreshCw } from "lucide-react";
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import ErrorBoundary from "@/components/ErrorBoundary";

interface AgentMessage {
  id: string;
  timestamp: string;
  type: string;
  symbol?: string;
  message: string;
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="h-4 w-[250px]" />
          <Skeleton className="h-20 w-full" />
        </div>
      ))}
    </div>
  );
}

function ErrorAlert({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  );
}

function AgentCommsContent() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const queryClient = useQueryClient();

  const { data: messages = [], isLoading: messagesLoading, error: messagesError } = useQuery<AgentMessage[]>({
    queryKey: ['/api/logs/agent-messages'],
    staleTime: 0,
    refetchInterval: autoRefresh ? 5000 : false
  });

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Agent Communications Log</h1>

      <div className="flex justify-between items-center mb-4">
        <Button
          size="sm"
          variant="outline"
          onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['/api/logs/agent-messages'] });
          }}
          disabled={messagesLoading}
        >
          {messagesLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span className="ml-1">Refresh</span>
        </Button>

        <Button
          size="sm"
          variant={autoRefresh ? "default" : "outline"}
          onClick={() => setAutoRefresh(!autoRefresh)}
        >
          Auto-refresh {autoRefresh ? "ON" : "OFF"}
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Executive Summaries</CardTitle>
        </CardHeader>
        <CardContent>
          {messagesError && (
            <div className="mb-4">
              <ErrorAlert message={
                (messagesError as Error)?.message ||
                'An error occurred while fetching messages'
              } />
            </div>
          )}

          <ScrollArea className="h-[600px]">
            {messagesLoading ? (
              <LoadingSkeleton />
            ) : messages.length === 0 ? (
              <div className="text-center p-4 text-muted-foreground">
                No agent communications found.
              </div>
            ) : (
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className="p-4 border rounded-lg bg-card"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="text-sm text-muted-foreground">
                        {new Date(message.timestamp).toLocaleString()}
                      </div>
                      {message.symbol && (
                        <Badge>{message.symbol}</Badge>
                      )}
                    </div>

                    <div className="prose dark:prose-invert max-w-none">
                      <p className="text-base leading-relaxed">
                        {message.message}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}

export default function AgentCommsPage() {
  return (
    <ErrorBoundary>
      <AgentCommsContent />
    </ErrorBoundary>
  );
}