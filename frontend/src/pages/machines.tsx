// src/pages/machines.tsx
import React, { useState, useEffect } from 'react';
import { getMachines, addMachine, deleteMachine } from '../lib/api';
import AddMachineForm from '../components/AddMachineForm/AddMachineForm';
import { AlertCircle, X } from 'lucide-react';

interface Machine {
  id: number;
  name: string;
  host: string;
  port: number;
  user: string;
  created_at: string;
  updated_at: string | null;
}

export default function MachinesPage() {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadMachines = async () => {
    try {
      const list = await getMachines();
      setMachines(list);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load machines');
    }
  };

  useEffect(() => {
    loadMachines();
  }, []);

  const handleDelete = async (host: string) => {
    if (!confirm('Are you sure you want to delete this machine?')) {
      return;
    }

    try {
      await deleteMachine(host);
      await loadMachines();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete machine');
    }
  };

  const handleAdd = async (data: {
    name: string;
    host: string;
    user: string;
    port: number;
    password?: string;
    ssh_key?: string;
  }) => {
    setIsLoading(true);
    try {
      await addMachine(data);
      await loadMachines();
      setError(null);
    } catch (err) {
      console.error('Error adding machine:', err);
      setError(err instanceof Error ? err.message : 'Failed to add machine');
      throw err; // Re-throw to let the form handle the error state
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Hosts</h2>
      
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg relative">
          <div className="flex items-start">
            <AlertCircle className="text-red-500 mr-2 flex-shrink-0 mt-0.5" size={20} />
            <div className="flex-grow">
              <h3 className="text-red-700 font-semibold">Error</h3>
              <p className="text-red-600">{error}</p>
            </div>
          </div>
          <button 
            onClick={() => setError(null)}
            className="absolute top-4 right-4 text-red-400 hover:text-red-600"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <AddMachineForm onAdd={handleAdd} />
      
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">Registered Hosts</h3>
        <div className="space-y-2">
          {machines.map((machine) => (
            <div 
              key={machine.host} 
              className="flex items-center justify-between bg-white p-4 rounded-lg shadow"
            >
              <div className="space-y-1">
                <div>
                  <strong className="text-lg">{machine.name}</strong>
                  <span className="ml-2 text-gray-600">({machine.host})</span>
                </div>
                <div className="text-sm text-gray-500">
                  {machine.user}@{machine.host}:{machine.port}
                </div>
              </div>
              <button 
                onClick={() => handleDelete(machine.host)} 
                className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors"
                disabled={isLoading}
              >
                Delete
              </button>
            </div>
          ))}
          {machines.length === 0 && (
            <div className="text-gray-500 text-center py-8 bg-gray-50 rounded-lg">
              No machines registered yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}