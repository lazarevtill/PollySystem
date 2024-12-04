import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatDate } from "@/lib/utils";

interface Activity {
  id: string;
  type: string;
  description: string;
  timestamp: string;
  status?: 'success' | 'error' | 'warning';
}

interface ActivityLogProps {
  activities: Activity[];
}

export function ActivityLog({ activities }: ActivityLogProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {activities.map((activity) => (
            <div
              key={activity.id}
              className="flex items-center space-x-4 rounded-md p-2 hover:bg-accent/50"
            >
              <div className={cn(
                "h-2 w-2 rounded-full",
                activity.status === 'error' && "bg-red-500",
                activity.status === 'warning' && "bg-yellow-500",
                activity.status === 'success' && "bg-green-500",
                !activity.status && "bg-blue-500"
              )} />
              <div className="flex-1 space-y-1">
                <p className="text-sm font-medium">{activity.type}</p>
                <p className="text-sm text-muted-foreground">
                  {activity.description}
                </p>
              </div>
              <div className="text-sm text-muted-foreground">
                {formatDate(activity.timestamp)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
