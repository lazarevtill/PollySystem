# /opt/infra-manager/frontend/src/components/machines/MachineDialog.tsx
import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/use-toast";
import { endpoints } from '@/lib/api';

const formSchema = z.object({
  name: z.string().min(1, "Name is required")
    .regex(/^[a-z0-9-]+$/, "Name can only contain lowercase letters, numbers, and hyphens"),
  hostname: z.string()
    .min(1, "Hostname is required")
    .regex(/^[a-z0-9-]+\.in\.lc$/, "Must be a valid .in.lc domain"),
  ssh_user: z.string().min(1, "SSH user is required"),
  ssh_port: z.coerce.number()
    .int()
    .min(1, "Port must be greater than 0")
    .max(65535, "Port must be less than 65536"),
});

interface MachineDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function MachineDialog({ open, onOpenChange, onSuccess }: MachineDialogProps) {
  const { toast } = useToast();
  const [publicKey, setPublicKey] = React.useState<string | null>(null);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: "",
      hostname: "",
      ssh_user: "",
      ssh_port: 22,
    },
  });

  const onSubmit = async (values: z.infer<typeof formSchema>) => {
    try {
      const response = await endpoints.machines.create(values);
      setPublicKey(response.data.public_key);
      
      toast({
        title: "Machine added successfully",
        description: "The SSH public key has been generated and needs to be added to the machine.",
      });
      
      form.reset();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.response?.data?.detail || "Failed to add machine",
        variant: "destructive",
      });
    }
  };

  const handleClose = () => {
    setPublicKey(null);
    form.reset();
    onOpenChange(false);
  };

  const handleCopyKey = async () => {
    if (publicKey) {
      await navigator.clipboard.writeText(publicKey);
      toast({
        title: "Copied",
        description: "SSH public key copied to clipboard",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add New Machine</DialogTitle>
          <DialogDescription>
            Add a new machine to your infrastructure. The machine must be accessible via VPN.
          </DialogDescription>
        </DialogHeader>

        {publicKey ? (
          <div className="space-y-4">
            <div className="space-y-2">
              <h3 className="font-medium">SSH Public Key</h3>
              <p className="text-sm text-muted-foreground">
                Add this public key to the machine's authorized_keys file:
              </p>
              <pre className="bg-muted p-4 rounded-md text-sm overflow-x-auto">
                {publicKey}
              </pre>
            </div>
            <DialogFooter className="flex justify-between">
              <Button variant="outline" onClick={handleClose}>Done</Button>
              <Button onClick={handleCopyKey}>Copy Key</Button>
            </DialogFooter>
          </div>
        ) : (
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
                    <FormDescription>
                      A unique identifier for this machine
                    </FormDescription>
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
                    <FormDescription>
                      The VPN hostname ending with .in.lc
                    </FormDescription>
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
                    <FormDescription>
                      The user for SSH connections
                    </FormDescription>
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
                        onChange={e => field.onChange(parseInt(e.target.value))}
                      />
                    </FormControl>
                    <FormDescription>
                      The SSH port (default: 22)
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter>
                <Button variant="outline" onClick={handleClose}>Cancel</Button>
                <Button type="submit">Add Machine</Button>
              </DialogFooter>
            </form>
          </Form>
        )}
      </DialogContent>
    </Dialog>
  );
}