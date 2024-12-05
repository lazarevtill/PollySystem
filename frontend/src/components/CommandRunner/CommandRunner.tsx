import React, { useState } from 'react';
import { runCommandAll } from '../../lib/api';

export default function CommandRunner() {
  const [command, setCommand] = useState("");
  const [results, setResults] = useState<Record<string, string>>({});

  const handleRun = async () => {
    const res = await runCommandAll(command);
    setResults(res.results);
  };

  return (
    <div className="mt-8">
      <h4 className="text-lg font-semibold mb-4">Execute Command</h4>
      <div className="flex space-x-4 mb-4">
        <input 
          value={command} 
          onChange={e => setCommand(e.target.value)} 
          placeholder="Enter command" 
          className="flex-grow px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button 
          onClick={handleRun}
          className="bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Run on All Hosts
        </button>
      </div>
      <div className="bg-gray-100 p-4 rounded-md">
        {Object.keys(results).map((host) => (
          <div key={host} className="mb-4 last:mb-0">
            <strong className="block mb-1">{host}:</strong>
            <pre className="bg-white p-2 rounded-md whitespace-pre-wrap break-all text-sm">
              {results[host]}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}

