import React, { useState } from 'react';

interface AddMachineFormProps {
  onAdd: (data: { name: string; host: string; user: string; password?: string }) => void;
}

export default function AddMachineForm({ onAdd }: AddMachineFormProps) {
  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [user, setUser] = useState("root");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onAdd({ name, host, user, password });
    setName("");
    setHost("");
    setUser("root");
    setPassword("");
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <h3 className="text-xl font-semibold mb-4">Add Machine</h3>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Name:</label>
        <input 
          value={name} 
          onChange={e => setName(e.target.value)} 
          required 
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Host:</label>
        <input 
          value={host} 
          onChange={e => setHost(e.target.value)} 
          required 
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">User:</label>
        <input 
          value={user} 
          onChange={e => setUser(e.target.value)} 
          required 
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Password (optional):</label>
        <input 
          value={password} 
          onChange={e => setPassword(e.target.value)} 
          type="password" 
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <button 
        type="submit" 
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        Add Machine
      </button>
    </form>
  );
}

