import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";

export default function MarketAnalysis() {
  const [analysis, setAnalysis] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const fetchAnalysis = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/analyze');
      const data = await response.json();
      
      if (data.response) {
        setAnalysis(data.response);
      } else {
        throw new Error('Invalid response format');
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to fetch market analysis",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Market Analysis</h1>
        <Button 
          onClick={fetchAnalysis} 
          disabled={loading}
        >
          {loading ? "Fetching..." : "Refresh Analysis"}
        </Button>
      </div>

      <Card className="p-6">
        {analysis ? (
          <div className="whitespace-pre-wrap">
            {analysis}
          </div>
        ) : (
          <div className="text-muted-foreground text-center py-8">
            Click the refresh button to fetch market analysis
          </div>
        )}
      </Card>
    </div>
  );
}
