import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Box,
  ExternalLink,
  PlayCircle,
  StopCircle,
  Terminal,
  Trash2,
  Plus,
} from 'lucide-react';
import { endpoints } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { DeploymentDialog } from './DeploymentDialog';
import { LogsDialog } from './LogsDialog';
import { useToast } from "@/components/ui/use-toast";

export function DeploymentList() {
  const [isDeployDialogOpen, setIsDeployDialogOpen] = React.useState(false);
  const [isLogsDialogOpen, setIsLogsDialogOpen] = React.useState(false);
  const [selectedDeployment, setSelectedDeployment] = React.useState<any>(null);
  const { toast } = useToast();

  const {
    data: deployments,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['deployments'],
    queryFn: async () => {
      const response = await endpoints.deployments.list();
      return response.data;
    }
  });

  const handleDelete = async (deploymentId: number) => {
    try {
      await endpoints.deployments.delete(deploymentId);
      toast({
        title: "Success",
        description: "Deployment deleted successfully",
      });
      refetch();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete deployment",
        variant: "destructive",
      });
    }
  };

  const handleStatusChange = async (deploymentId: number, action: 'start' | 'stop') => {
    try {
      await endpoints.deployments[action](deploymentId);
      toast({
        title: "Success",
        description: `Deployment ${action}ed successfully`,
      });
      refetch();
    } catch (error) {
      toast({
        title: "Error",
        description: `Failed to ${action} deployment`,
        variant: "destructive",
      });
    }
  };

  const viewLogs = async (deployment: any) => {
    setSelectedDeployment(deployment);
    setIsLogsDialogOpen(true);
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error loading deployments</div>;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'warning';
      case 'failed':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Deployments</h1>
        <div className="space-x-2">
          <Button onClick={() => setIsDeployDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" /> New Deployment
          </Button>
        </div>
      </div>

      <div className="grid gap-6">
        {deployments?.map((deployment) => (
          <Card key={deployment.id}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center space-x-4">
                <Box className="h-6 w-6 text-muted-foreground" />
                <div>
                  <CardTitle>{deployment.name}</CardTitle>
                  <CardDescription>
                    {deployment.deployment_type} on {deployment.machine.name}
                  </CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={getStatusColor(deployment.status)}>
                  {deployment.status}
                </Badge>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => window.open(`https://${deployment.subdomain}`, '_blank')}
                >
                  <ExternalLink className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => viewLogs(deployment)}
                >
                  <Terminal className="h-4 w-4" />
                </Button>
                {deployment.status === 'running' ? (
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleStatusChange(deployment.id, 'stop')}
                  >
                    <StopCircle className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => handleStatusChange(deployment.id, 'start')}
                  >
                    <PlayCircle className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="destructive"
                  size="icon"
                  onClick={() => handleDelete(deployment.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium">Subdomain</p>
                  <p className="text-sm text-muted-foreground">
                    {deployment.subdomain}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Created</p>
                  <p className="text-sm text-muted-foreground">
                    {formatDate(deployment.created_at)}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Last Updated</p>
                  <p className="text-sm text-muted-foreground">
                    {deployment.updated_at ? formatDate(deployment.updated_at) : 'Never'}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <DeploymentDialog
        open={isDeployDialogOpen}
        onOpenChange={setIsDeployDialogOpen}
        onSuccess={() => {
          setIsDeployDialogOpen(false);
          refetch();
        }}
      />

      {selectedDeployment && (
        <LogsDialog
          deployment={selectedDeployment}
          open={isLogsDialogOpen}
          onOpenChange={setIsLogsDialogOpen}
        />
      )}
    </>
  );
}
        description: "Failed to delete machine",
        variant: "destructive",
      });
    }
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error loading machines</div>;
  }

  return (
    <>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Machines</h1>
        <Button onClick={() => setIsDialogOpen(true)}>
          <Plus className="mr-2 h-4 w-4" /> Add Machine
        </Button>
      </div>

      <div className="grid gap-6">
        {machines?.map((machine) => (
          <Card key={machine.id}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <div className="flex items-center space-x-4">
                <Server className="h-6 w-6 text-muted-foreground" />
                <div>
                  <CardTitle>{machine.name}</CardTitle>
                  <CardDescription>{machine.hostname}</CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={machine.is_active ? "default" : "secondary"}>
                  {machine.is_active ? "Active" : "Inactive"}
                </Badge>
                <Button
                  variant="destructive"
                  size="icon"
                  onClick={() => handleDelete(machine.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <p className="text-sm font-medium">SSH User</p>
                  <p className="text-sm text-muted-foreground">
                    {machine.ssh_user}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">SSH Port</p>
                  <p className="text-sm text-muted-foreground">
                    {machine.ssh_port}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium">Deployments</p>
                  <p className="text-sm text-muted-foreground">
                    {machine.deployments_count}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <MachineDialog
        open={isDialogOpen}
        onOpenChange={setIsDialogOpen}
        onSuccess={() => {
          setIsDialogOpen(false);
          refetch();
        }}
      />
    </>
  );
}

