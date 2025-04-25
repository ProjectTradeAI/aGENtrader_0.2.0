import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Trade } from '@shared/schema';

interface OpenTradesTableProps {
  trades: Trade[];
  onSymbolSelect: (symbol: string) => void;
}

const OpenTradesTable: React.FC<OpenTradesTableProps> = ({ trades, onSymbolSelect }) => {
  const openTrades = trades.filter(trade => trade.status === 'executed');
  
  // Calculate PNL and position size for each trade
  const tradeStats = openTrades.reduce((acc, trade) => {
    if (!acc[trade.symbol]) {
      acc[trade.symbol] = {
        totalValue: 0,
        pnl: 0,
        percentSize: 0
      };
    }
    
    const value = trade.price * trade.quantity;
    acc[trade.symbol].totalValue += value;
    // Simple PNL calculation - can be enhanced with current market price
    acc[trade.symbol].pnl = ((trade.price - trade.price * 0.95) * trade.quantity);
    acc[trade.symbol].percentSize = 25; // Placeholder - calculate based on portfolio value
    
    return acc;
  }, {} as Record<string, { totalValue: number; pnl: number; percentSize: number }>);

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle>Open Trades</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2">Symbol</th>
                <th className="text-right py-2">Size %</th>
                <th className="text-right py-2">PNL</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(tradeStats).map(([symbol, stats]) => (
                <tr 
                  key={symbol} 
                  className="border-b cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => onSymbolSelect(symbol)}
                >
                  <td className="py-2">{symbol}</td>
                  <td className="text-right py-2">{stats.percentSize.toFixed(1)}%</td>
                  <td className={`text-right py-2 ${stats.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    ${Math.abs(stats.pnl).toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
};

export default OpenTradesTable;
