// src/hooks/usePlugins.ts
import { useState, useEffect } from 'react';
import { Plugin } from '../plugins/types';
import { pluginRegistry } from '../plugins/registry';

export function usePlugins() {
  const [plugins, setPlugins] = useState<Plugin[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    const loadPlugins = async () => {
      try {
        const availablePlugins = pluginRegistry.getAllPlugins();
        
        // Initialize all plugins
        for (const plugin of availablePlugins) {
          await pluginRegistry.initializePlugin(plugin.metadata.name);
        }

        setPlugins(availablePlugins);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to load plugins'));
      } finally {
        setLoading(false);
      }
    };

    loadPlugins();
  }, []);

  return { plugins, loading, error };
}
