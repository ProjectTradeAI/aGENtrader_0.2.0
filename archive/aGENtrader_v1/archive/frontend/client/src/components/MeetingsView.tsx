import React, { useState, useEffect } from 'react';
import { useLocation } from 'wouter';
import axios from 'axios';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { ExecutiveSummary } from './ExecutiveSummary';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion";
import { Button } from "./ui/button";
import { ScrollArea } from "./ui/scroll-area";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "./ui/alert";
import { Separator } from "./ui/separator";
import { Skeleton } from "./ui/skeleton";
import { formatDistanceToNow } from 'date-fns';
import { 
  RefreshCw, 
  MessageCircle, 
  AlertTriangle, 
  Clock,
  CheckCircle,
  XCircle,
  HelpCircle 
} from 'lucide-react';

interface AgentStatement {
  agent: string;
  content: string;
}

interface Decision {
  symbol: string;
  signal: string;
  confidence: number;
  strategy: string;
  risk_profile: string;
  reason: string;
  timestamp: string;
  price: number;
}

interface SymbolDiscussion {
  topic: string;
  symbol: string;
  statements: AgentStatement[];
  decision: Decision | null;
}

interface PortfolioDiscussion {
  topic: string;
  statements: AgentStatement[];
}

interface Meeting {
  meeting_id: string;
  timestamp: string;
  participants: string[];
  discussions: (SymbolDiscussion | PortfolioDiscussion)[];
  decisions: Record<string, Decision>;
  meeting_duration: number;
  executive_summary?: ExecutiveSummary;
}

interface MeetingSummary {
  id: string;
  timestamp: string;
}

interface ExecutiveSummary {
  timestamp: string;
  meeting_type: string;
  market_overview: {
    market_trend: {
      direction: string;
      strength: number;
      timeframe: string;
    };
    key_indicators: {
      moving_averages: string;
      rsi: string;
      volume: string;
    };
    sentiment: string;
    key_levels: {
      nearest_support: number;
      nearest_resistance: number;
    };
  };
  trading_recommendation: {
    action: string;
    confidence: number;
    timeframe: string;
    key_reasons: string[];
    risk_profile: {
      position_size: number;
      stop_loss: number;
      take_profit: number;
    };
  };
  key_metrics: {
    participants: number;
    analysis_points: number;
    decisions_made: number;
  };
}

const getSignalColor = (signal: string) => {
  switch (signal?.toLowerCase()) {
    case 'buy':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case 'sell':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    case 'strong buy':
      return 'bg-green-200 text-green-900 dark:bg-green-800 dark:text-green-200';
    case 'strong sell':
      return 'bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-200';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
  }
};

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 75) return 'text-green-600 dark:text-green-400';
  if (confidence >= 50) return 'text-yellow-600 dark:text-yellow-400';
  return 'text-red-600 dark:text-red-400';
};

const getAgentColor = (agent: string) => {
  if (agent.includes('Market')) return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
  if (agent.includes('Sentiment')) return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300';
  if (agent.includes('Strategy')) return 'bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300';
  if (agent.includes('Liquidity')) return 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900 dark:text-cyan-300';
  if (agent.includes('Trade')) return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300';
  if (agent.includes('Quantum')) return 'bg-violet-100 text-violet-800 dark:bg-violet-900 dark:text-violet-300';
  if (agent.includes('On-Chain')) return 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300';
  return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300';
};

const getSignalIcon = (signal: string) => {
  switch (signal?.toLowerCase()) {
    case 'buy':
    case 'strong buy':
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    case 'sell':
    case 'strong sell':
      return <XCircle className="h-5 w-5 text-red-600" />;
    case 'hold':
    case 'neutral':
      return <HelpCircle className="h-5 w-5 text-gray-500" />;
    default:
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
  }
};

const MeetingsView: React.FC = () => {
  const [meetings, setMeetings] = useState<MeetingSummary[]>([]);
  const [currentMeeting, setCurrentMeeting] = useState<Meeting | null>(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [location, setLocation] = useLocation();
  const [activeTab, setActiveTab] = useState('meeting');

  const fetchMeetingsList = async () => {
    try {
      const response = await axios.get('/api/meetings');
      setMeetings(response.data);
    } catch (err) {
      console.error('Error fetching meetings list:', err);
      setError('Failed to load meetings list');
    }
  };

  const fetchLatestMeeting = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/meetings/latest');
      setCurrentMeeting(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching latest meeting:', err);
      setError('No meetings available yet');
      setCurrentMeeting(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchMeetingById = async (id: string) => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/meetings/${id}`);
      setCurrentMeeting(response.data);
      setError(null);
    } catch (err) {
      console.error(`Error fetching meeting ${id}:`, err);
      setError(`Failed to load meeting details for ${id}`);
      setCurrentMeeting(null);
    } finally {
      setLoading(false);
    }
  };

  const triggerMeeting = async () => {
    setTriggering(true);
    try {
      await axios.post('/api/meetings/trigger');
      setTimeout(() => {
        fetchLatestMeeting();
        fetchMeetingsList();
      }, 1000);
    } catch (err) {
      console.error('Error triggering meeting:', err);
      setError('Failed to trigger a new meeting');
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    const path = location.split('/');
    if (path.length >= 3 && path[1] === 'meetings') {
      const meetingId = path[2];
      if (meetingId === 'latest') {
        fetchLatestMeeting();
      } else {
        fetchMeetingById(meetingId);
      }
    } else {
      fetchLatestMeeting();
    }
    fetchMeetingsList();
  }, [location]);

  const renderDecisionSummary = () => {
    if (!currentMeeting || !currentMeeting.decisions || Object.keys(currentMeeting.decisions).length === 0) {
      return (
        <div className="p-4 text-center">
          <p className="text-gray-500 dark:text-gray-400">No trading decisions were made in this meeting</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Trading Decisions Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Object.entries(currentMeeting.decisions).map(([symbol, decision]) => (
            <Card key={symbol} className="overflow-hidden">
              <CardHeader className="pb-2">
                <div className="flex justify-between items-center">
                  <CardTitle className="text-xl">{symbol}</CardTitle>
                  <Badge className={getSignalColor(decision.signal)}>{decision.signal.toUpperCase()}</Badge>
                </div>
                <CardDescription>
                  {new Date(decision.timestamp).toLocaleString()}
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-2">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Strategy</span>
                    <span className="font-medium">{decision.strategy}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Confidence</span>
                    <span className={`font-medium ${getConfidenceColor(decision.confidence)}`}>
                      {decision.confidence}%
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Risk Profile</span>
                    <span className="font-medium">{decision.risk_profile}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500 dark:text-gray-400">Price</span>
                    <span className="font-medium">${decision.price?.toFixed(2) || 'N/A'}</span>
                  </div>
                </div>
              </CardContent>
              <CardFooter className="pt-2">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {decision.reason}
                </p>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  const renderMeetingDiscussions = () => {
    if (!currentMeeting) return null;

    return (
      <Accordion type="single" collapsible className="w-full">
        {currentMeeting.discussions.map((discussion, idx) => (
          <AccordionItem key={idx} value={`discussion-${idx}`}>
            <AccordionTrigger>
              <div className="flex items-center gap-2">
                <span>{discussion.topic}</span>
                {('symbol' in discussion && discussion.decision) && (
                  <Badge className={getSignalColor(discussion.decision.signal)}>
                    {discussion.decision.signal.toUpperCase()}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>
            <AccordionContent>
              <div className="space-y-4 py-2">
                {discussion.statements.map((statement, statementIdx) => (
                  <div key={statementIdx} className="rounded-lg bg-white dark:bg-gray-800 p-4 shadow-sm">
                    <div className="flex items-start gap-3">
                      <Badge variant="outline" className={`${getAgentColor(statement.agent)} whitespace-nowrap`}>
                        {statement.agent.replace(' Agent', '')}
                      </Badge>
                      <p className="text-sm">{statement.content}</p>
                    </div>
                  </div>
                ))}
              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    );
  };

  const renderMeetingsList = () => {
    if (meetings.length === 0) {
      return (
        <div className="text-center p-4">
          <p className="text-gray-500 dark:text-gray-400">No meetings available</p>
        </div>
      );
    }

    return (
      <ScrollArea className="h-[400px]">
        <div className="space-y-2 p-2">
          {meetings.map((meeting) => {
            const isActive = currentMeeting?.meeting_id === meeting.id;
            return (
              <div
                key={meeting.id}
                className={`
                  flex items-center justify-between p-3 rounded-md cursor-pointer
                  hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors
                  ${isActive ? 'bg-gray-100 dark:bg-gray-800' : ''}
                `}
                onClick={() => setLocation(`/meetings/${meeting.id}`)}
              >
                <div className="flex items-center gap-3">
                  <Clock className="h-4 w-4 text-gray-500" />
                  <div>
                    <p className="text-sm font-medium">Meeting {meeting.id.split('_')[1]}</p>
                    <p className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(meeting.timestamp))} ago
                    </p>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={(e) => {
                    e.stopPropagation();
                    setLocation(`/meetings/${meeting.id}`);
                  }}
                >
                  <MessageCircle className="h-4 w-4" />
                  <span className="sr-only">View</span>
                </Button>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    );
  };


  if (loading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-64" />
          <Skeleton className="h-10 w-24" />
        </div>
        <Skeleton className="h-64 w-full" />
        <div className="space-y-2">
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Agent Meetings</h2>
          <p className="text-muted-foreground">
            View strategic discussions and decisions from agent meetings
          </p>
        </div>
        <Button
          onClick={triggerMeeting}
          disabled={triggering}
        >
          {triggering ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Triggering...
            </>
          ) : (
            <>
              <MessageCircle className="mr-2 h-4 w-4" />
              Trigger Meeting
            </>
          )}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {currentMeeting?.executive_summary && (
        <ExecutiveSummary summary={currentMeeting.executive_summary} />
      )}

      {currentMeeting && (
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-xl">
                Meeting Summary {currentMeeting.meeting_id.split('_')[1]}
              </CardTitle>
              <Badge variant="outline" className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDistanceToNow(new Date(currentMeeting.timestamp))} ago
              </Badge>
            </div>
            <CardDescription>
              {new Date(currentMeeting.timestamp).toLocaleString()}
              {' · '}
              Duration: {(currentMeeting.meeting_duration / 60).toFixed(1)} minutes
              {' · '}
              Participants: {currentMeeting.participants.length}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs
              defaultValue="decisions"
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="decisions">Decisions</TabsTrigger>
                <TabsTrigger value="meeting">Full Discussion</TabsTrigger>
              </TabsList>
              <TabsContent value="decisions" className="py-4">
                {renderDecisionSummary()}
              </TabsContent>
              <TabsContent value="meeting" className="py-4">
                {renderMeetingDiscussions()}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="md:col-span-3">
          <CardHeader>
            <CardTitle>Previous Meetings</CardTitle>
            <CardDescription>
              Review past agent discussions and trading decisions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {renderMeetingsList()}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Meeting Statistics</CardTitle>
            <CardDescription>
              Agent activity metrics
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Total Meetings</span>
                <span className="font-medium">{meetings.length}</span>
              </div>
              <Separator />
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Meeting Frequency</span>
                <span className="font-medium">Every 15 min</span>
              </div>
              <Separator />
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Active Agents</span>
                <span className="font-medium">
                  {currentMeeting?.participants?.length || 0}
                </span>
              </div>
              <Separator />
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-500">Latest Meeting</span>
                <span className="font-medium">
                  {currentMeeting
                    ? formatDistanceToNow(new Date(currentMeeting.timestamp)) + ' ago'
                    : 'N/A'}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MeetingsView;