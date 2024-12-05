// src/App.tsx
import React from 'react';
import { usePlugins } from './hooks/usePlugins';

const App: React.FC = () => {
  const { plugins, loading, error } = usePlugins();

  if (loading) {
    return <div>Loading plugins...</div>;
  }

  if (error) {
    return <div>Error loading plugins: {error.message}</div>;
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">PollySystem Dashboard</h1>
      
      <div className="grid grid-cols-1 gap-6">
        {plugins.map(plugin => (
          <div key={plugin.metadata.name}>
            <h2 className="text-xl font-semibold mb-4">
              {plugin.metadata.description}
            </h2>
            <plugin.Component />
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
