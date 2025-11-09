import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { AlertCircle, Download, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { apiService } from '@/services/apiService';

// ============================================================================
// Types
// ============================================================================

interface NLUStats {
  total_prompts: number;
  total_prompts_today: number;
  total_prompts_week: number;
  avg_confidence: number;
  avg_confidence_today: number;
  low_confidence_count: number;
  failed_workflows: number;
  correction_count: number;
  intent_distribution: Array<{ intent: string; count: number }>;
  confidence_distribution: Array<{ bucket: string; count: number }>;
  workflow_success_rate: Record<string, { total: number; success: number; rate: number }>;
}

interface PromptLog {
  id: string;
  user_id: string;
  prompt: string;
  predicted_intent: string;
  confidence: number;
  corrected_intent?: string;
  correction_notes?: string;
  was_successful?: boolean;
  workflow_type?: string;
  execution_error?: string;
  created_at: string;
}

// ============================================================================
// Main Component
// ============================================================================

export default function AdminNLUPage() {
  const [activeTab, setActiveTab] = useState('overview');

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">NLU Monitoring</h1>
        <p className="text-muted-foreground">
          Model performance, data quality, and retraining workflow
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="low-confidence">Low Confidence</TabsTrigger>
          <TabsTrigger value="failed">Failed Workflows</TabsTrigger>
          <TabsTrigger value="corrections">Corrections</TabsTrigger>
          <TabsTrigger value="exports">Exports</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab />
        </TabsContent>

        <TabsContent value="low-confidence">
          <LowConfidenceTab />
        </TabsContent>

        <TabsContent value="failed">
          <FailedWorkflowsTab />
        </TabsContent>

        <TabsContent value="corrections">
          <CorrectionsTab />
        </TabsContent>

        <TabsContent value="exports">
          <ExportsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ============================================================================
// Overview Tab
// ============================================================================

function OverviewTab() {
  const { data: stats, isLoading } = useQuery<NLUStats>({
    queryKey: ['admin', 'nlu', 'stats'],
    queryFn: async () => {
      const response = await apiService.get('/v1/admin/nlu/stats?days=7');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  if (!stats) {
    return <div className="text-center p-8">No data available</div>;
  }

  const totalIntentCount = stats.intent_distribution.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Prompts (7d)"
          value={stats.total_prompts_week.toLocaleString()}
          subtitle={`${stats.total_prompts_today} today`}
          icon={<Activity className="h-4 w-4" />}
        />
        <MetricCard
          title="Avg Confidence"
          value={`${(stats.avg_confidence * 100).toFixed(1)}%`}
          subtitle={`${(stats.avg_confidence_today * 100).toFixed(1)}% today`}
          trend={stats.avg_confidence_today > stats.avg_confidence ? 'up' : 'down'}
        />
        <MetricCard
          title="Low Confidence"
          value={stats.low_confidence_count.toString()}
          subtitle="Need review (<70%)"
          variant="warning"
        />
        <MetricCard
          title="Failed Workflows"
          value={stats.failed_workflows.toString()}
          subtitle="Execution errors"
          variant="error"
        />
      </div>

      {/* Intent Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Intent Distribution (Top 10)</CardTitle>
          <CardDescription>Last 7 days</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {stats.intent_distribution.slice(0, 10).map((item, index) => {
            const percentage = (item.count / totalIntentCount) * 100;
            return (
              <div key={item.intent} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{item.intent}</span>
                  <span className="text-muted-foreground">{item.count} ({percentage.toFixed(1)}%)</span>
                </div>
                <Progress value={percentage} className="h-2" />
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Confidence Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>Confidence Distribution</CardTitle>
          <CardDescription>Last 7 days</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {stats.confidence_distribution.map((item) => {
            const total = stats.confidence_distribution.reduce((sum, i) => sum + i.count, 0);
            const percentage = (item.count / total) * 100;
            return (
              <div key={item.bucket} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium">{item.bucket}</span>
                  <span className="text-muted-foreground">{item.count} ({percentage.toFixed(1)}%)</span>
                </div>
                <Progress value={percentage} className="h-2" />
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Workflow Success Rates */}
      <Card>
        <CardHeader>
          <CardTitle>Workflow Success Rates by Intent</CardTitle>
          <CardDescription>Intents with the most failures</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Intent</TableHead>
                <TableHead className="text-right">Total</TableHead>
                <TableHead className="text-right">Success</TableHead>
                <TableHead className="text-right">Success Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(stats.workflow_success_rate)
                .sort(([, a], [, b]) => a.rate - b.rate)
                .slice(0, 10)
                .map(([intent, data]) => (
                  <TableRow key={intent}>
                    <TableCell className="font-medium">{intent}</TableCell>
                    <TableCell className="text-right">{data.total}</TableCell>
                    <TableCell className="text-right">{data.success}</TableCell>
                    <TableCell className="text-right">
                      <Badge variant={data.rate < 70 ? 'destructive' : 'default'}>
                        {data.rate.toFixed(1)}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// Low Confidence Tab
// ============================================================================

function LowConfidenceTab() {
  const [selectedLog, setSelectedLog] = useState<PromptLog | null>(null);
  const [correctedIntent, setCorrectedIntent] = useState('');
  const [correctionNotes, setCorrectionNotes] = useState('');
  const queryClient = useQueryClient();

  const { data: prompts, isLoading } = useQuery<PromptLog[]>({
    queryKey: ['admin', 'nlu', 'low-confidence'],
    queryFn: async () => {
      const response = await apiService.get('/v1/admin/nlu/low-confidence?threshold=0.7&limit=100');
      return response.data;
    },
  });

  const addCorrectionMutation = useMutation({
    mutationFn: async ({ logId, correctedIntent, correctionNotes }: {
      logId: string;
      correctedIntent: string;
      correctionNotes?: string;
    }) => {
      await apiService.post('/v1/admin/nlu/correct-intent', {
        log_id: logId,
        corrected_intent: correctedIntent,
        correction_notes: correctionNotes,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'nlu'] });
      setSelectedLog(null);
      setCorrectedIntent('');
      setCorrectionNotes('');
    },
  });

  if (isLoading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  return (
    <div className="space-y-4">
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          These prompts have confidence scores below 70%. Review them to add manual corrections for model retraining.
        </AlertDescription>
      </Alert>

      {selectedLog && (
        <Card className="border-blue-500">
          <CardHeader>
            <CardTitle>Add Correction</CardTitle>
            <CardDescription>Prompt: "{selectedLog.prompt}"</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium">Predicted Intent (Confidence: {(selectedLog.confidence * 100).toFixed(1)}%)</label>
              <Input value={selectedLog.predicted_intent} disabled />
            </div>
            <div>
              <label className="text-sm font-medium">Corrected Intent *</label>
              <Input
                value={correctedIntent}
                onChange={(e) => setCorrectedIntent(e.target.value)}
                placeholder="Enter correct intent"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Notes (optional)</label>
              <Textarea
                value={correctionNotes}
                onChange={(e) => setCorrectionNotes(e.target.value)}
                placeholder="Why was this corrected?"
                rows={3}
              />
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => {
                  if (correctedIntent) {
                    addCorrectionMutation.mutate({
                      logId: selectedLog.id,
                      correctedIntent,
                      correctionNotes,
                    });
                  }
                }}
                disabled={!correctedIntent || addCorrectionMutation.isPending}
              >
                Save Correction
              </Button>
              <Button variant="outline" onClick={() => setSelectedLog(null)}>
                Cancel
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Low Confidence Prompts ({prompts?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Prompt</TableHead>
                <TableHead>Predicted Intent</TableHead>
                <TableHead className="text-right">Confidence</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {prompts?.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="max-w-md truncate">{log.prompt}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{log.predicted_intent}</Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant={log.confidence < 0.5 ? 'destructive' : 'secondary'}>
                      {(log.confidence * 100).toFixed(1)}%
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(log.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-right">
                    <Button size="sm" variant="outline" onClick={() => setSelectedLog(log)}>
                      Correct
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// Failed Workflows Tab
// ============================================================================

function FailedWorkflowsTab() {
  const { data: prompts, isLoading } = useQuery<PromptLog[]>({
    queryKey: ['admin', 'nlu', 'failed-workflows'],
    queryFn: async () => {
      const response = await apiService.get('/v1/admin/nlu/failed-workflows?limit=100');
      return response.data;
    },
  });

  if (isLoading) {
    return <div className="text-center p-8">Loading...</div>;
  }

  return (
    <div className="space-y-4">
      <Alert>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          These prompts led to workflow execution failures. Investigate errors and add corrections if needed.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <CardTitle>Failed Workflows ({prompts?.length || 0})</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Prompt</TableHead>
                <TableHead>Intent</TableHead>
                <TableHead>Workflow</TableHead>
                <TableHead>Error</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {prompts?.map((log) => (
                <TableRow key={log.id}>
                  <TableCell className="max-w-md truncate">{log.prompt}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{log.predicted_intent}</Badge>
                  </TableCell>
                  <TableCell>{log.workflow_type || 'N/A'}</TableCell>
                  <TableCell className="max-w-xs truncate text-red-600 text-sm">
                    {log.execution_error || 'Unknown error'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(log.created_at).toLocaleDateString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// Corrections Tab
// ============================================================================

function CorrectionsTab() {
  return (
    <div className="space-y-4">
      <Alert>
        <AlertDescription>
          View all manually corrected prompts. These are used for model retraining.
        </AlertDescription>
      </Alert>
      <Card>
        <CardContent className="pt-6 text-center text-muted-foreground">
          Corrections view - Coming soon
        </CardContent>
      </Card>
    </div>
  );
}

// ============================================================================
// Exports Tab
// ============================================================================

function ExportsTab() {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (mode: 'retraining' | 'review') => {
    setIsExporting(true);
    try {
      const response = await apiService.post('/v1/admin/nlu/export-training-data', {
        days: 30,
        mode,
      });

      // Download as JSON file
      const dataStr = JSON.stringify(response.data.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `nlu_${mode}_${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-4">
      <Alert>
        <AlertDescription>
          Export production data for model retraining or manual review.
        </AlertDescription>
      </Alert>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Export Training Data</CardTitle>
            <CardDescription>
              Corrected prompts + high-confidence predictions for retraining
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => handleExport('retraining')}
              disabled={isExporting}
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Export Training Data (Last 30 Days)
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Export Review Queue</CardTitle>
            <CardDescription>
              Low-confidence prompts for manual labeling
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => handleExport('review')}
              disabled={isExporting}
              variant="outline"
              className="w-full"
            >
              <Download className="h-4 w-4 mr-2" />
              Export Review Queue
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ============================================================================
// Metric Card Component
// ============================================================================

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: React.ReactNode;
  trend?: 'up' | 'down';
  variant?: 'default' | 'warning' | 'error';
}

function MetricCard({ title, value, subtitle, icon, trend, variant = 'default' }: MetricCardProps) {
  const colorClasses = {
    default: 'border-l-blue-500',
    warning: 'border-l-yellow-500',
    error: 'border-l-red-500',
  };

  return (
    <Card className={`border-l-4 ${colorClasses[variant]}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {subtitle && (
          <div className="flex items-center text-xs text-muted-foreground mt-1">
            {trend && (
              trend === 'up' ? (
                <TrendingUp className="h-3 w-3 mr-1 text-green-500" />
              ) : (
                <TrendingDown className="h-3 w-3 mr-1 text-red-500" />
              )
            )}
            {subtitle}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
