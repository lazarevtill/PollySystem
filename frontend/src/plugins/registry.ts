// src/plugins/registry.ts
import { Plugin, PluginMetadata } from './types';

class PluginRegistry {
  private plugins: Map<string, Plugin> = new Map();
  private initialized: Set<string> = new Set();

  async registerPlugin(plugin: Plugin): Promise<void> {
    const { name } = plugin.metadata;
    
    if (this.plugins.has(name)) {
      throw new Error(`Plugin ${name} is already registered`);
    }

    // Check dependencies
    for (const dep of plugin.metadata.dependencies) {
      if (!this.plugins.has(dep)) {
        throw new Error(`Plugin ${name} requires ${dep} which is not loaded`);
      }
    }

    this.plugins.set(name, plugin);
  }

  async initializePlugin(name: string): Promise<void> {
    if (this.initialized.has(name)) return;

    const plugin = this.plugins.get(name);
    if (!plugin) {
      throw new Error(`Plugin ${name} not found`);
    }

    // Initialize dependencies first
    for (const dep of plugin.metadata.dependencies) {
      await this.initializePlugin(dep);
    }

    await plugin.initialize();
    this.initialized.add(name);
  }

  getPlugin(name: string): Plugin | undefined {
    return this.plugins.get(name);
  }

  getAllPlugins(): Plugin[] {
    return Array.from(this.plugins.values());
  }
}

export const pluginRegistry = new PluginRegistry();
