import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Machine {
  id: number;
  name: string;
  hostname: string;
  ssh_user: string;
  ssh_port: number;
  is_active: boolean;
  deployments_count: number;
  created_at: string;
}

export interface Deployment {
  id: number;
  name: string;
  machine_id: number;
  deployment_type: 'container' | 'compose';
  config: any;
  subdomain: string;
  status: 'running' | 'stopped' | 'failed';
  created_at: string;
  updated_at: string;
  machine: Machine;
}

export interface SystemStats {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_deployments: number;
  total_machines: number;
  recent_events: Array<{
    id: number;
    type: string;
    message: string;
    timestamp: string;
  }>;
}

// API endpoints
export const endpoints = {
  // Machines
  machines: {
    list: () => api.get<Machine[]>('/machines'),
    create: (data: Partial<Machine>) => api.post<Machine>('/machines', data),
    delete: (id: number) => api.delete(`/machines/${id}`),
  },
  
  // Deployments
  deployments: {
    list: () => api.get<Deployment[]>('/deployments'),
    createContainer: (data: any) => api.post('/deployments/container', data),
    createCompose: (data: FormData) => api.post('/deployments/compose', data),
    delete: (id: number) => api.delete(`/deployments/${id}`),
    stop: (id: number) => api.post(`/deployments/${id}/stop`),
    start: (id: number) => api.post(`/deployments/${id}/start`),
    logs: (id: number) => api.get(`/deployments/${id}/logs`),
  },
  
  // System
  system: {
    stats: () => api.get<SystemStats>('/system/stats'),
    health: () => api.get('/health'),
  },
};

export default api;
