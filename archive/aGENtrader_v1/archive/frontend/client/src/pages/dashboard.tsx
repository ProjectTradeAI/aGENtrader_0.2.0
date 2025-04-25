import { Button } from "../components/ui/button";
import TradingViewChart from "../components/TradingViewChart";
import PortfolioOverview from "../components/PortfolioOverview";
import TradeHistory from "../components/TradeHistory";
import AgentActivity from "../components/AgentActivity";
import StrategyPerformance from "../components/StrategyPerformance";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import TradingSignals from "../components/TradingSignals";
import MarketSummary from "../components/MarketSummary";
import { ArrowUpRight } from "lucide-react";

export default function Dashboard() {
  const defaultSymbol = "BTCUSDT";

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <div className="flex items-center space-x-2">
          <Button>
            <ArrowUpRight className="mr-2 h-4 w-4" />
            Deploy changes
          </Button>
        </div>
      </div>
      <Tabs defaultValue="agents" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trading">Trading</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MarketSummary />
          </div>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
            <div className="col-span-4">
              <TradingViewChart symbol={defaultSymbol} />
            </div>
            <div className="col-span-3">
              <PortfolioOverview />
            </div>
          </div>
          <div className="grid gap-4 grid-cols-1">
            <TradeHistory />
          </div>
        </TabsContent>
        <TabsContent value="agents" className="space-y-4">
          <div className="grid gap-4 grid-cols-1">
            <AgentActivity />
          </div>
        </TabsContent>
        <TabsContent value="analytics" className="space-y-4">
          <div className="grid gap-4 grid-cols-1">
            <StrategyPerformance />
          </div>
        </TabsContent>
        <TabsContent value="trading" className="space-y-4">
          <div className="grid gap-4 grid-cols-1">
            <TradingSignals />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}