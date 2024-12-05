// src/plugins/machines/index.tsx
import React from 'react';
import { Plugin, PluginMetadata } from '../types';
import MachineManagement from './MachineManagement';

const machineManagementPlugin: Plugin = {
  metadata: {
    name: 'machine_management',
    version: '1.0.0',
    description: 'Manages remote machines and their connections',
    dependencies: [],
    requiresAuth: true,
  },
  
  Component: MachineManagement,

  async initialize() {
    // Initialize plugin
    console.log('Initializing machine management plugin');
  },

  async cleanup() {
    // Cleanup plugin resources
    console.log('Cleaning up machine management plugin');
  }
};

// Register plugin
pluginRegistry.registerPlugin(machineManagementPlugin);
