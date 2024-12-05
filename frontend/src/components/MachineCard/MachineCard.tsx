// src/components/MachineCard/MachineCard.tsx
import React from 'react';
import { AlertCircle } from 'lucide-react';

interface MachineProps {
  name: string;
  host: string;
  cpuUsage: number;
  memUsed: number;
  memTotal: number;
  error?: string;
}

export default function MachineCard({ 
  name, 
  host, 
  cpuUsage, 
  memUsed, 
  memTotal,
  error 
}: MachineProps) {
  const memPercent = ((memUsed / memTotal) * 100).toFixed(1);

  if (error) {
    return (
      <div className="bg-white border border-red-200 rounded-lg p-4 w-64 shadow-sm">
        <div className="flex items-center space-x-2 mb-2">
          <AlertCircle className="text-red-500" size={20} />
          <h3 className="text-lg font-semibold">{name}</h3>
        </div>
        <p className="text-gray-600 mb-2">{host}</p>
        <p className="text-red-500 text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 w-64 shadow-sm">
      <h3 className="text-lg font-semibold mb-2">{name}</h3>
      <p className="text-gray-600 mb-4">{host}</p>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">CPU:</span>
          <strong className="text-sm">{cpuUsage.toFixed(1)}%</strong>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">Memory:</span>
          <strong className="text-sm">{memUsed}/{memTotal} MB ({memPercent}%)</strong>
        </div>
      </div>
    </div>
  );
}