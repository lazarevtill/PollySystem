import { useToast } from "@/components/ui/use-toast";

export function useCustomToast() {
  const { toast } = useToast();

  return {
    success: (message: string) => {
      toast({
        title: "Success",
        description: message,
        variant: "default",
      });
    },
    error: (message: string) => {
      toast({
        title: "Error",
        description: message,
        variant: "destructive",
      });
    },
    warning: (message: string) => {
      toast({
        title: "Warning",
        description: message,
        variant: "default",
        className: "bg-yellow-500",
      });
    },
  };
}
