import { useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { queryClient } from "@/lib/queryClient";
import { useWebSocket } from "@/hooks/use-websocket";
import type { Trade } from "@shared/schema";

interface TradingSocketOptions {
  defaultSymbol?: string;
  onAnalysisUpdate?: (symbol: string) => void;
}

export function useTradingSocket(options: TradingSocketOptions = {}) {
  const { toast } = useToast();
  const defaultSymbol = options.defaultSymbol || "BTCUSDT";

  const { isConnected, error, sendMessage } = useWebSocket({
    path: '/trading-ws',
    onMessage: (data: any) => {
      try {
        console.log("[Trading Socket] Received data:", data);

        switch (data.type) {
          case "trade_update":
            const trade: Trade = data.trade;
            // Invalidate queries to refresh data
            queryClient.invalidateQueries({ queryKey: ["/api/trades"] });
            queryClient.invalidateQueries({ queryKey: ["/api/metrics"] });
            toast({
              title: "New Trade",
              description: `${trade.type.toUpperCase()} ${trade.quantity} ${trade.symbol} at $${trade.price}`,
            });
            break;

          case "connection_status":
            console.log("[Trading Socket] Connection status:", data.status);
            if (data.status === 'connected') {
              toast({
                title: "Connected",
                description: "Successfully connected to trading server",
                duration: 3000,
              });
            }
            break;

          case "analysis_update":
            toast({
              title: "Market Analysis",
              description: `New analysis received for ${data.symbol}`,
              duration: 3000,
            });
            queryClient.invalidateQueries({ queryKey: ["/api/analysis"] });
            options.onAnalysisUpdate?.(data.symbol);
            break;

          case "error":
            toast({
              title: "Trading Error",
              description: data.message,
              variant: "destructive",
            });
            break;

          default:
            console.log("[Trading Socket] Unhandled message type:", data.type);
        }
      } catch (error) {
        console.error('[Trading Socket] Error processing message:', error);
        toast({
          title: "Message Error",
          description: "Failed to process server message",
          variant: "destructive",
        });
      }
    },
    onError: (error: Error) => {
      console.error("[Trading Socket] Error:", error);
      toast({
        title: "Connection Error",
        description: error.message || "Error connecting to trading server",
        variant: "destructive",
      });
    },
    onClose: () => {
      toast({
        title: "Connection Lost",
        description: "Trading connection lost. Attempting to reconnect...",
        variant: "destructive",
      });
    },
    onOpen: () => {
      // Subscribe to default symbol when connected
      sendMessage({
        type: 'subscribe_symbol',
        symbol: defaultSymbol
      });
    }
  });

  // Monitor connection state changes
  useEffect(() => {
    if (isConnected) {
      console.log("[Trading Socket] Connected and ready");
    } else if (error) {
      console.error("[Trading Socket] Connection error:", error);
    }
  }, [isConnected, error]);

  return {
    isConnected,
    error,
    sendMessage,
    subscribeToSymbol: (symbol: string) => {
      sendMessage({
        type: 'subscribe_symbol',
        symbol
      });
    }
  };
}