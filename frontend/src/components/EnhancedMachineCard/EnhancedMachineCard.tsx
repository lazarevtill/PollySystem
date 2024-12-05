// File: ./frontend/src/components/EnhancedMachineCard/EnhancedMachineCard.tsx
import React, { useState } from 'react';
import { AlertCircle, ChevronDown, ChevronUp, Activity, HardDrive, Cpu, Server, Clock, User } from 'lucide-react';
import { ProgressBar } from '../ProgressBar/ProgressBar';

interface MachineCardProps {
  name: string;
  host: string;
  user: string;
  port: number;
  cpuUsage: number;
  memUsed: number;
  memTotal: number;
  error?: string;
  lastUpdated?: string;
}

const formatBytes = (bytes: number): string => {
  const mb = bytes / 1024 / 1024;
  return `${Math.round(mb * 100) / 100} MB`;
};

const getCPUColor = (usage: number): string => {
  if (usage >= 90) return 'bg-red-500';
  if (usage >= 70) return 'bg-orange-500';
  if (usage >= 50) return 'bg-yellow-500';
  return 'bg-green-500';
};

const getMemoryColor = (usage: number): string => {
  if (usage >= 90) return 'bg-red-500';
  if (usage >= 70) return 'bg-orange-500';
  if (usage >= 50) return 'bg-yellow-500';
  return 'bg-green-500';
};

export const EnhancedMachineCard: React.FC<MachineCardProps> = ({ 
  name, 
  host, 
  user,
  port,
  cpuUsage, 
  memUsed, 
  memTotal,
  error,
  lastUpdated
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const memPercent = ((memUsed / memTotal) * 100).toFixed(1);

  if (error) {
    return (
      <div className="bg-white border border-red-200 rounded-lg shadow-sm overflow-hidden">
        <div className="p-4">
          <div className="flex items-center space-x-2 mb-2">
            <AlertCircle className="text-red-500" size={20} />
            <h3 className="text-lg font-semibold">{name}</h3>
          </div>
          <p className="text-gray-600 mb-2">{host}</p>
          <p className="text-red-500 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      <div 
        className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <Server className="text-gray-500" size={20} />
              <h3 className="text-lg font-semibold">{name}</h3>
            </div>
            <p className="text-gray-600 mt-1">{host}</p>
          </div>
          <button className="text-gray-400 hover:text-gray-600">
            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <div className="flex justify-between items-center mb-1">
              <div className="flex items-center space-x-2">
                <Cpu size={16} className="text-gray-500" />
                <span className="text-sm text-gray-600">CPU Usage</span>
              </div>
              <span className="text-sm font-medium">{cpuUsage.toFixed(1)}%</span>
            </div>
            <ProgressBar value={cpuUsage} max={100} color={getCPUColor(cpuUsage)} />
          </div>

          <div>
            <div className="flex justify-between items-center mb-1">
              <div className="flex items-center space-x-2">
                <HardDrive size={16} className="text-gray-500" />
                <span className="text-sm text-gray-600">Memory Usage</span>
              </div>
              <span className="text-sm font-medium">{memPercent}%</span>
            </div>
            <ProgressBar value={parseFloat(memPercent)} max={100} color={getMemoryColor(parseFloat(memPercent))} />
          </div>
        </div>
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200 bg-gray-50 p-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-sm">
                <User size={16} className="text-gray-500" />
                <span className="text-gray-600">User:</span>
                <span className="font-medium">{user}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Server size={16} className="text-gray-500" />
                <span className="text-gray-600">Port:</span>
                <span className="font-medium">{port}</span>
              </div>
            </div>
            <div className="space-y-1">
              <div className="flex items-center space-x-2 text-sm">
                <Activity size={16} className="text-gray-500" />
                <span className="text-gray-600">Status:</span>
                <span className="font-medium text-green-600">Active</span>
              </div>
              <div className="flex items-center space-x-2 text-sm">
                <Clock size={16} className="text-gray-500" />
                <span className="text-gray-600">Last Updated:</span>
                <span className="font-medium">{lastUpdated || 'Just now'}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 space-y-2">
            <div className="p-3 bg-white rounded border border-gray-200">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Detailed Memory Usage</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Used Memory:</span>
                  <span className="ml-2 font-medium">{formatBytes(memUsed * 1024 * 1024)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Total Memory:</span>
                  <span className="ml-2 font-medium">{formatBytes(memTotal * 1024 * 1024)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
