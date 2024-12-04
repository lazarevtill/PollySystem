import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { endpoints } from '@/lib/api';
import { RefreshCw } from 'lucide-react';
import { usePolling } from '@/hooks/use-polling';

interface LogsDialogProps {
  deployment: {
    id: number;
    name: string;
  };
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function LogsDialog({ deployment, open, onOpenChange }: LogsDialogProps) {
  const {
    data,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['deployment-logs', deployment.id],
    queryFn: async () => {
      const response = await endpoints.deployments.logs(deployment.id);
      return response.data;
    },
    enabled: open,
    refetchOnWindowFocus: false,
  });

  // Auto-refresh logs every 5 seconds when dialog is open
  usePolling(() => {
    if (open) {
      refetch();
    }
  }, 5000);

  const formatLogs = (logs: string) => {
    return logs.split('\n').map((line, index) => {
      // Add color based on log level
      let className = 'text-muted-foreground';
      if (line.toLowerCase().includes('error')) {
        className = 'text-red-500';
      } else if (line.toLowerCase().includes('warn')) {
        className = 'text-yellow-500';
      } else if (line.toLowerCase().includes('info')) {
        className = 'text-blue-500';
      }

      return (
return (
        <div key={index} className={cn('py-1 font-mono text-sm', className)}>
          {line}
        </div>
      );
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Logs: {deployment.name}</span>
            <Button
              variant="outline"
              size="icon"
              onClick={() => refetch()}
              className="h-8 w-8"
              disabled={isLoading}
            >
              <RefreshCw className={cn(
                "h-4 w-4",
                isLoading && "animate-spin"
              )} />
            </Button>
          </DialogTitle>
        </DialogHeader>

        <ScrollArea className="flex-1 p-4 bg-muted rounded-md">
          {isLoading && (
            <div className="flex items-center justify-center h-full">
              <RefreshCw className="h-6 w-6 animate-spin" />
            </div>
          )}

          {error && (
            <div className="flex items-center justify-center h-full text-red-500">
              Failed to load logs
            </div>
          )}

          {data && (
            <div className="space-y-1">
              {formatLogs(data.logs)}
            </div>
          )}
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
}

