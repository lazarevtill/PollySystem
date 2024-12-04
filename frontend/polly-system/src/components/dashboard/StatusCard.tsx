import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface StatusCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  description?: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
}

export function StatusCard({ title, value, icon, description, trend }: StatusCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {trend && (
          <div className={`text-xs ${trend.isPositive ? 'text-green-500' : 'text-red-500'} mt-1`}>
            {trend.isPositive ? '↑' : '↓'} {trend.value}%
          </div>
        )}
      </CardContent>
    </Card>
  );
}
