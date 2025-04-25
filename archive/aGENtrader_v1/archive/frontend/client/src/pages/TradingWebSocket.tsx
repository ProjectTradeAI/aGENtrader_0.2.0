import { useState, useEffect } from 'react';
import { useTradingSocket } from '@/hooks/use-trading-socket';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

export default function TradingWebSocket() {
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [messages, setMessages] = useState<string[]>([]);
  const { toast } = useToast();

  const { isConnected, error, sendMessage, subscribeToSymbol } = useTradingSocket({
    defaultSymbol: symbol,
    onAnalysisUpdate: (symbol) => {
      setMessages(prev => [...prev, `Received analysis update for ${symbol}`]);
    }
  });

  const handleSubscribe = () => {
    if (symbol.trim()) {
      subscribeToSymbol(symbol.toUpperCase());
      toast({
        title: "Subscription",
        description: `Subscribed to ${symbol}`,
      });
    }
  };

  const requestAnalysis = () => {
    sendMessage({
      type: 'request_analysis',
      symbol: symbol
    });
    toast({
      title: "Analysis Requested",
      description: `Requested analysis for ${symbol}`,
    });
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Trading WebSocket</h1>
      
      <div className={`p-3 mb-4 rounded ${isConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
        Status: {isConnected ? 'Connected' : 'Disconnected'}
        {error && <div className="text-red-600 mt-1">Error: {error}</div>}
      </div>

      <div className="mb-4 flex gap-2">
        <Input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          placeholder="Enter symbol (e.g. BTCUSDT)"
          className="flex-1"
        />
        <Button
          onClick={handleSubscribe}
          disabled={!isConnected || !symbol.trim()}
          variant="outline"
        >
          Subscribe
        </Button>
        <Button
          onClick={requestAnalysis}
          disabled={!isConnected || !symbol.trim()}
        >
          Request Analysis
        </Button>
      </div>

      <div className="border rounded p-4 h-[400px] overflow-y-auto">
        {messages.map((msg, i) => (
          <div key={i} className="py-1">
            <span className="text-gray-500 text-sm">
              {new Date().toLocaleTimeString()}
            </span>
            : {msg}
          </div>
        ))}
      </div>
    </div>
  );
}
