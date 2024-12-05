import React, { useEffect, useState } from 'react';
import { getMachines, getMachineMetrics } from '../lib/api';
import { EnhancedMachineCard } from '../components/EnhancedMachineCard';
import CommandRunner from '../components/CommandRunner/CommandRunner';
import { AlertCircle } from 'lucide-react';

interface MachineState {
  id: number;
  name: string;
  host: string;
  user: string;
  port: number;
  cpuUsage: number;
  memUsed: number;
  memTotal: number;
  error?: string;
  lastUpdate?: string;
}

export default function Home() {
  const [machines, setMachines] = useState<MachineState[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMachines = async () => {
      try {
        const machineList = await getMachines();
        const updated = await Promise.all(
          machineList.map(async (m) => {
            try {
              const metrics = await getMachineMetrics(m.host);
              return {
                ...m,
                cpuUsage: metrics.cpu_usage_percent,
                memUsed: metrics.memory_used_mb,
                memTotal: metrics.memory_total_mb,
                error: metrics.status === 'error' ? metrics.error : undefined,
                lastUpdate: new Date().toLocaleTimeString()
              };
            } catch (err) {
              console.error(`Failed to fetch metrics for ${m.host}:`, err);
              return {
                ...m,
                cpuUsage: 0,
                memUsed: 0,
                memTotal: 1,
                error: err instanceof Error ? err.message : 'Failed to fetch metrics'
              };
            }
          })
        );
        setMachines(updated);
      } catch (err) {
        console.error('Failed to fetch machines:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch machines');
      }
    };

    fetchMachines();
    const interval = setInterval(fetchMachines, 30000); // Refresh every 30 seconds

    return () => clearInterval(interval);
  }, []);

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex items-center space-x-2">
          <AlertCircle className="text-red-500" size={20} />
          <h2 className="text-xl font-bold text-red-700">Error</h2>
        </div>
        <p className="text-red-600 mt-2">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">System Status</h2>
        <div className="text-sm text-gray-500">
          Auto-refreshes every 30 seconds
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {machines.map((m) => (
          <EnhancedMachineCard
            key={m.host}
            name={m.name}
            host={m.host}
            user={m.user}
            port={m.port}
            cpuUsage={m.cpuUsage}
            memUsed={m.memUsed}
            memTotal={m.memTotal}
            error={m.error}
            lastUpdated={m.lastUpdate}
          />
        ))}
      </div>

      {machines.length === 0 && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500">No machines registered yet</p>
          <p className="text-sm text-gray-400 mt-2">
            Add machines in the Hosts section to monitor them here
          </p>
        </div>
      )}

      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Command Center</h3>
        <CommandRunner />
      </div>
    </div>
  );
}