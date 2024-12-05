import React from 'react';

interface MachineProps {
  name: string;
  host: string;
  cpuUsage: number;
  memUsed: number;
  memTotal: number;
}

export default function MachineCard({ name, host, cpuUsage, memUsed, memTotal }: MachineProps) {
  const memPercent = ((memUsed / memTotal) * 100).toFixed(1);

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

