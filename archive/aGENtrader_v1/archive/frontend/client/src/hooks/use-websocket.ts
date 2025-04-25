import { useEffect, useRef, useState, useCallback } from 'react';

interface WebSocketHookProps {
  path: string;
  onMessage?: (data: any) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Error) => void;
}

export function useWebSocket({
  path,
  onMessage,
  onOpen,
  onClose,
  onError
}: WebSocketHookProps) {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}${path}`;

      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        onOpen?.();
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        onClose?.();
      };

      wsRef.current.onerror = (event) => {
        const wsError = new Error('WebSocket error occurred');
        setError(wsError.message);
        console.error('WebSocket error:', event);
        onError?.(wsError);
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data);
        } catch {
          onMessage?.(event.data);
        }
      };
    } catch (err) {
      const connectionError = err instanceof Error ? err : new Error('Failed to connect to WebSocket');
      setError(connectionError.message);
      console.error('WebSocket connection error:', connectionError);
      onError?.(connectionError);
    }
  }, [path, onMessage, onOpen, onClose, onError]);

  const sendMessage = useCallback((message: string | object) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      const wsError = new Error('WebSocket is not connected');
      setError(wsError.message);
      onError?.(wsError);
      return;
    }

    try {
      const data = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(data);
    } catch (err) {
      const sendError = err instanceof Error ? err : new Error('Failed to send message');
      setError(sendError.message);
      console.error('Error sending message:', sendError);
      onError?.(sendError);
    }
  }, [onError]);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return {
    isConnected,
    error,
    sendMessage
  };
}