import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Server, Trash2, Terminal, RefreshCw } from 'lucide-react';

// Machine Card Component with System Metrics
const MachineCard = ({ machine, onDelete, onRefresh }) => {
  const memoryUsagePercent = machine.system_info 
    ? (machine.system_info.memory_used / machine.system_info.memory_total) * 100 
    : 0;
  const diskUsagePercent = machine.system_info
    ? (machine.system_info.disk_used / machine.system_info.disk_total) * 100
    : 0;

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>{machine.name}</CardTitle>
          <div className="text-sm text-gray-500">{machine.ip_address}</div>
        </div>
        <div className="flex space-x-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onRefresh(machine.id)}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => onDelete(machine.id)}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              machine.status === 'active' ? 'bg-green-500' : 'bg-red-500'
            }`} />
            <span className="text-sm">{machine.status}</span>
          </div>

          {/* System Metrics */}
          {machine.system_info && (
            <div className="space-y-2">
              {/* CPU Usage */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>CPU Usage</span>
                  <span>{machine.system_info.cpu_usage.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${Math.min(machine.system_info.cpu_usage, 100)}%` }}
                  />
                </div>
              </div>

              {/* Memory Usage */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Memory Usage</span>
                  <span>{memoryUsagePercent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${memoryUsagePercent}%` }}
                  />
                </div>
              </div>

              {/* Disk Usage */}
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>Disk Usage</span>
                  <span>{diskUsagePercent.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${diskUsagePercent}%` }}
                  />
                </div>
              </div>

              {/* Docker Status */}
              <div className="flex items-center justify-between">
                <span className="text-sm">Docker Status</span>
                <span className={`text-sm ${
                  machine.system_info.docker_status ? 'text-green-500' : 'text-red-500'
                }`}>
                  {machine.system_info.docker_status ? 'Running' : 'Stopped'}
                </span>
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

// Command Executor Component
const CommandExecutor = ({ onExecute }) => {
  const [command, setCommand] = useState('');
  const [executing, setExecuting] = useState(false);
  const [results, setResults] = useState(null);

  const handleExecute = async () => {
    setExecuting(true);
    try {
      const results = await onExecute(command);
      setResults(results);
    } catch (error) {
      console.error('Command execution failed:', error);
    } finally {
      setExecuting(false);
    }
  };

  return (
    <Card className="w-full mb-6">
      <CardHeader>
        <CardTitle>Execute Command on All Machines</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex space-x-2 mb-4">
          <Input
            value={command}
            onChange={(e) => setCommand(e.target.value)}
            placeholder="Enter command to execute"
            disabled={executing}
          />
          <Button onClick={handleExecute} disabled={!command || executing}>
            {executing ? <Loader2 className="animate-spin" /> : <Terminal className="h-4 w-4" />}
          </Button>
        </div>

        {results && (
          <div className="space-y-2">
            {Object.entries(results).map(([machineId, result]) => (
              <div key={machineId} className="border rounded p-2">
                <div className="font-medium">Machine ID: {machineId}</div>
                <div className="mt-1">
                  {result.success ? (
                    <pre className="whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
                      {result.stdout}
                    </pre>
                  ) : (
                    <div className="text-sm text-red-500">
                      Error: {result.stderr}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Main Machine Management Component
const MachineManagement = () => {
  const [machines, setMachines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newMachine, setNewMachine] = useState({
    name: '',
    ip_address: '',
    ssh_key: ''
  });

  useEffect(() => {
    fetchMachines();
    // Refresh machine data every 30 seconds
    const interval = setInterval(fetchMachines, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchMachines = async () => {
    try {
      const response = await fetch('/api/v1/machines');
      if (!response.ok) throw new Error('Failed to fetch machines');
      const data = await response.json();
      setMachines(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMachine = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await fetch('/api/v1/machines', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...newMachine,
          id: crypto.randomUUID(), // Generate a unique ID for the machine
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add machine');
      }
      
      setNewMachine({ name: '', ip_address: '', ssh_key: '' });
      fetchMachines();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMachine = async (machineId) => {
    try {
      const response = await fetch(`/api/v1/machines/${machineId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete machine');
      
      setMachines(prev => prev.filter(m => m.id !== machineId));
    } catch (err) {
      setError(err.message);
    }
  };

  const handleExecuteCommand = async (command) => {
    try {
      const response = await fetch('/api/v1/machines/command', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ command })
      });

      if (!response.ok) throw new Error('Failed to execute command');
      
      return await response.json();
    } catch (err) {
      setError(err.message);
      return null;
    }
  };

  const handleRefreshMachine = async (machineId) => {
    await fetchMachines();
  };

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <h1 className="text-3xl font-bold mb-6">Machine Management</h1>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <CommandExecutor onExecute={handleExecuteCommand} />

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Add New Machine</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleAddMachine} className="space-y-4">
            <Input
              placeholder="Machine Name"
              value={newMachine.name}
              onChange={e => setNewMachine(prev => ({
                ...prev,
                name: e.target.value
              }))}
              required
            />
            <Input
              placeholder="IP Address"
              value={newMachine.ip_address}
              onChange={e => setNewMachine(prev => ({
                ...prev,
                ip_address: e.target.value
              }))}
              required
            />
            <div>
              <label className="block text-sm font-medium mb-2">SSH Private Key</label>
              <textarea
                className="w-full min-h-[100px] p-2 border rounded"
                placeholder="Paste your SSH private key here"
                value={newMachine.ssh_key}
                onChange={e => setNewMachine(prev => ({
                  ...prev,
                  ssh_key: e.target.value
                }))}
                required
              />
            </div>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : 'Add Machine'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {machines.map(machine => (
          <MachineCard
            key={machine.id}
            machine={machine}
            onDelete={handleDeleteMachine}
            onRefresh={handleRefreshMachine}
          />
        ))}
      </div>
    </div>
  );
};

export default MachineManagement;