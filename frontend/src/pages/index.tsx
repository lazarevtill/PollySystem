import React, { useEffect, useState } from 'react';
import { getMachines, getMachineMetrics } from '../lib/api';
import MachineCard from '../components/MachineCard/MachineCard';
import CommandRunner from '../components/CommandRunner/CommandRunner';

export default function Home() {
  const [machines, setMachines] = useState<any[]>([]);

  useEffect(() => {
    const fetchMachines = async () => {
      const machineList = await getMachines();
      const updated = await Promise.all(machineList.map(async (m) => {
        const metrics = await getMachineMetrics(m.host);
        return {
          ...m,
          cpuUsage: metrics.cpu_usage_percent,
          memUsed: metrics.memory_used_mb,
          memTotal: metrics.memory_total_mb
        };
      }));
      setMachines(updated);
    };

    fetchMachines();
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Status</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {machines.map((m) => (
          <MachineCard
            key={m.host}
            name={m.name}
            host={m.host}
            cpuUsage={m.cpuUsage}
            memUsed={m.memUsed}
            memTotal={m.memTotal}
          />
        ))}
      </div>
      <h3 className="text-xl font-semibold mt-8 mb-4">Run command on all hosts:</h3>
      <CommandRunner />
    </div>
  );
}

