import React, { useEffect, useRef, useState } from 'react';
import type { Trade } from '@shared/schema';

interface TradingViewChartProps {
  symbol: string;
  theme?: 'light' | 'dark';
  width?: string | number;
  height?: string | number;
  interval?: string;
  trades?: Trade[];
}

export const TradingViewChart: React.FC<TradingViewChartProps> = ({
  symbol,
  theme = 'dark',
  width = '100%',
  height = 500,
  interval = '1D',
  trades = []
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [currentSymbol, setCurrentSymbol] = useState(symbol);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const widgetRef = useRef<any>(null);

  useEffect(() => {
    let widget: any = null;
    let isMounted = true;

    const initializeChart = async () => {
      try {
        const container = containerRef.current;
        if (!container || !isMounted) return;

        // Clear container
        while (container.firstChild) {
          container.removeChild(container.firstChild);
        }

        // Create widget container
        const widgetContainer = document.createElement('div');
        widgetContainer.id = 'tradingview-widget-container';
        widgetContainer.style.height = '100%';
        widgetContainer.style.width = '100%';
        container.appendChild(widgetContainer);

        // Ensure TradingView script is loaded
        await new Promise<void>((resolve, reject) => {
          if (typeof window.TradingView !== 'undefined') {
            resolve();
            return;
          }

          const script = document.createElement('script');
          script.src = 'https://s3.tradingview.com/tv.js';
          script.async = true;
          script.onload = () => resolve();
          script.onerror = () => reject(new Error('Failed to load TradingView widget'));
          document.head.appendChild(script);
        });

        if (!isMounted) return;

        // Create widget
        widget = new window.TradingView.widget({
          autosize: true,
          symbol: `BINANCE:${currentSymbol}USD`,
          interval: interval,
          timezone: 'Etc/UTC',
          theme: theme,
          style: '1',
          locale: 'en',
          toolbar_bg: '#f1f3f6',
          enable_publishing: false,
          allow_symbol_change: true,
          container_id: 'tradingview-widget-container',
          overrides: {
            "mainSeriesProperties.style": 1,
            "paneProperties.background": theme === 'dark' ? "#1a1a1a" : "#ffffff",
            "paneProperties.vertGridProperties.color": theme === 'dark' ? "#363c4e" : "#e9e9ea",
            "paneProperties.horzGridProperties.color": theme === 'dark' ? "#363c4e" : "#e9e9ea",
          },
          studies_overrides: {
            "volume.volume.color.0": theme === 'dark' ? "#363c4e" : "#e9e9ea",
            "volume.volume.color.1": theme === 'dark' ? "#363c4e" : "#e9e9ea",
          },
          loading_screen: { backgroundColor: theme === 'dark' ? "#1a1a1a" : "#ffffff" },
          onChartReady: () => {
            if (!isMounted) return;
            setIsLoading(false);

            // Add trade markers
            setTimeout(() => {
              if (!isMounted) return;
              trades.forEach(trade => {
                if (trade.symbol === currentSymbol) {
                  const markerColor = trade.type === 'buy' ? '#22c55e' : '#ef4444';
                  const markerShape = trade.type === 'buy' ? 'arrow_up' : 'arrow_down';
                  const markerText = `${trade.type.toUpperCase()} ${trade.quantity} ${currentSymbol}`;
                  const markerTooltip = `Price: $${trade.price}\nQuantity: ${trade.quantity}\nType: ${trade.type.toUpperCase()}`;

                  try {
                    widget.activeChart().createShape(
                      {
                        time: Math.floor(new Date(trade.timestamp).getTime() / 1000),
                        price: trade.price,
                        channel: 'trade_signals'
                      },
                      {
                        shape: markerShape,
                        text: markerText,
                        tooltip: markerTooltip,
                        overrides: {
                          backgroundColor: markerColor,
                          borderColor: markerColor,
                          textColor: theme === 'dark' ? '#ffffff' : '#000000',
                          fontsize: 12,
                          bold: true
                        }
                      }
                    );
                  } catch (error) {
                    console.error('Error adding marker:', error);
                  }
                }
              });
            }, 1000);
          }
        });

        widgetRef.current = widget;
      } catch (error) {
        if (isMounted) {
          console.error('Chart initialization error:', error);
          setError(error instanceof Error ? error.message : 'Failed to initialize chart');
          setIsLoading(false);
        }
      }
    };

    initializeChart();

    return () => {
      isMounted = false;
      if (widget) {
        try {
          widget.remove();
        } catch (error) {
          console.error('Error removing widget:', error);
        }
      }
    };
  }, [currentSymbol, theme, interval, trades]);

  // Update current symbol when prop changes
  useEffect(() => {
    setCurrentSymbol(symbol);
  }, [symbol]);

  if (error) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-red-50 dark:bg-red-900/20 rounded-lg p-4">
        <p className="text-red-600 dark:text-red-400">Error: {error}</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-background">
        <div className="animate-pulse text-muted-foreground">Loading chart...</div>
      </div>
    );
  }

  return (
    <div className="w-full h-full flex flex-col">
      <div className="flex space-x-2 mb-4">
        {['BTC', 'ETH', 'SOL'].map((sym) => (
          <button 
            key={sym}
            className={`px-3 py-1 rounded ${currentSymbol === sym ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}
            onClick={() => setCurrentSymbol(sym)}
          >
            {sym}
          </button>
        ))}
      </div>
      <div ref={containerRef} className="flex-1" />
    </div>
  );
};

export default TradingViewChart;

declare global {
  interface Window {
    TradingView: any;
  }
}