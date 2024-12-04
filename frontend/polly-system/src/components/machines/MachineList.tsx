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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Server, Trash2, Plus } from 'lucide-react';
import { endpoints } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { MachineDialog } from './MachineDialog';
import { useToast } from "@/components/ui/use-toast";

export function MachineList() {
  const [isDialogOpen, setIsDialogOpen] = React.useState(false);
  const { toast } = useToast();

  const {
    data: machines,
    isLoading,
    error,
    refetch
  } = useQuery({
    queryKey: ['machines'],
    queryFn: async () => {
      const response = await endpoints.machines.list();
      return response.data;
    }
  });

  const handleDelete = async (machineId: number) => {
    try {
      await endpoints.machines.delete(machineId);
      toast({
        title: "Success",
        description: "Machine deleted successfully",
      });
      refetch();
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to add machine. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add New Machine</DialogTitle>
          <DialogDescription>
            Add a new machine to your infrastructure. Make sure the machine is accessible via VPN.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="production-1" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="hostname"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Hostname</FormLabel>
                  <FormControl>
                    <Input placeholder="server1.in.lc" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="ssh_user"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>SSH User</FormLabel>
                  <FormControl>
                    <Input placeholder="ubuntu" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="ssh_port"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>SSH Port</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end space-x-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit">Add Machine</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
