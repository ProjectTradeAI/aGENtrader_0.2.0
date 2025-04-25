import { QueryClientProvider } from "@tanstack/react-query";
import { queryClient } from "./lib/queryClient";
import { Switch, Route } from "wouter";
import { Toaster } from "@/components/ui/toaster";
import { ThemeProvider } from "@/components/theme-provider";
import NotFound from "@/pages/not-found";
import Dashboard from "@/pages/dashboard";
import { Navigation } from "@/components/navigation";
import ErrorBoundary from "./components/ErrorBoundary";
import { Suspense, lazy } from "react";

// Lazy load components to improve initial load time
const MarketAnalysis = lazy(() => import("@/pages/market-analysis"));
const AgentComms = lazy(() => import("@/pages/agent-comms"));
const TradingWebSocket = lazy(() => import("@/pages/TradingWebSocket"));

// Create placeholder components for routes that don't have implementations yet
const PlaceholderPage = ({ title }: { title: string }) => (
  <div className="flex flex-col items-center justify-center min-h-[70vh]">
    <h1 className="text-3xl font-bold mb-4">{title}</h1>
    <p className="text-lg text-muted-foreground mb-8">This page is under construction</p>
    <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
  </div>
);

const TradesPage = () => <PlaceholderPage title="Trades Dashboard" />;
const SettingsPage = () => <PlaceholderPage title="Settings" />;

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen bg-background">
      <div className="text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ErrorBoundary>
          <div className="min-h-screen bg-background">
            <div className="border-b">
              <div className="flex h-16 items-center px-4">
                <h2 className="text-lg font-bold tracking-tight">Trading Bot</h2>
                <Navigation className="mx-6" />
              </div>
            </div>
            <Suspense fallback={<LoadingFallback />}>
              <div className="container mx-auto py-6">
                <Switch>
                  <Route path="/" component={Dashboard} />
                  <Route path="/dashboard" component={Dashboard} />
                  <Route path="/market-analysis" component={MarketAnalysis} />
                  <Route path="/agent-comms" component={AgentComms} />
                  <Route path="/trading-ws" component={TradingWebSocket} />
                  <Route path="/trades" component={TradesPage} />
                  <Route path="/settings" component={SettingsPage} />
                  <Route component={NotFound} />
                </Switch>
              </div>
            </Suspense>
            <Toaster />
          </div>
        </ErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;