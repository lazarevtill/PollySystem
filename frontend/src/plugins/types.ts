// src/plugins/types.ts
export interface PluginMetadata {
    name: string;
    version: string;
    description: string;
    dependencies: string[];
    requiresAuth: boolean;
  }
  
  export interface Plugin {
    metadata: PluginMetadata;
    Component: React.ComponentType;
    initialize: () => Promise<void>;
    cleanup: () => Promise<void>;
  }