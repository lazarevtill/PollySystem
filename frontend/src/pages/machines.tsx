import React, { useState, useEffect } from 'react';
import { getMachines, addMachine, deleteMachine } from '../lib/api';
import AddMachineForm from '../components/AddMachineForm/AddMachineForm';

export default function MachinesPage() {
  const [machines, setMachines] = useState<any[]>([]);

  const loadMachines = async () => {
    const list = await getMachines();
    setMachines(list);
  };

  useEffect(() => {
    loadMachines();
  }, []);

  const handleDelete = async (host: string) => {
    await deleteMachine(host);
    loadMachines();
  };

  const handleAdd = async (data: any) => {
    await addMachine(data);
    loadMachines();
  };

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Hosts</h2>
      <AddMachineForm onAdd={handleAdd} />
      <ul className="mt-4 space-y-2">
        {machines.map((m) => (
          <li key={m.host} className="flex items-center justify-between bg-white p-4 rounded-lg shadow">
            <div>
              <strong className="text-lg">{m.name}</strong>
              <span className="ml-2 text-gray-600">({m.host})</span>
            </div>
            <button 
              onClick={() => handleDelete(m.host)} 
              className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors"
            >
              Delete
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

