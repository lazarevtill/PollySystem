// src/lib/api.ts

interface Machine {
  id: number;
  name: string;
  host: string;
  port: number;
  user: string;
  created_at: string;
  updated_at: string | null;
}

interface MachineMetrics {
  cpu_usage_percent: number;
  memory_used_mb: number;
  memory_total_mb: number;
  status: string;
  error?: string;
}

interface MachineCreate {
  name: string;
  host: string;
  user: string;
  port?: number;
  password?: string;
  ssh_key?: string;
}

interface CommandResult {
  results: Record<string, string>;
}

export async function getMachines(): Promise<Machine[]> {
  const res = await fetch('http://localhost:8000/api/v1/machines');
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch machines");
  }
  return await res.json();
}

export async function getMachineMetrics(host: string): Promise<MachineMetrics> {
  const res = await fetch(`http://localhost:8000/api/v1/machines/${host}/metrics`);
  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch metrics");
  }
  return await res.json();
}

export async function addMachine(data: MachineCreate): Promise<Machine> {
  const requestBody: MachineCreate = {
    name: data.name.trim(),
    host: data.host.trim(),
    user: data.user.trim(),
    port: data.port || 22
  };

  if (data.password) {
    requestBody.password = data.password;
  } else if (data.ssh_key) {
    let formattedKey = data.ssh_key.trim();
    if (!formattedKey.endsWith('\n')) {
      formattedKey += '\n';
    }
    requestBody.ssh_key = formattedKey;
  }

  const res = await fetch('http://localhost:8000/api/v1/machines', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(requestBody)
  });

  if (!res.ok) {
    const errorData = await res.json();
    console.error('Server error response:', errorData);
    throw new Error(errorData.detail || errorData.message || "Failed to add machine");
  }

  return await res.json();
}

export async function deleteMachine(host: string): Promise<{ status: string }> {
  const res = await fetch(`http://localhost:8000/api/v1/machines/${host}`, {
    method: 'DELETE'
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to delete machine");
  }
  return await res.json();
}

export async function runCommandAll(command: string): Promise<CommandResult> {
  if (!command.trim()) {
    throw new Error("Command cannot be empty");
  }

  const res = await fetch('http://localhost:8000/api/v1/commands/run_all', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ command })
  });

  if (!res.ok) {
    const error = await res.json();
    // Safely handle detail
    const detailMessage = typeof error.detail === 'string'
      ? error.detail
      : JSON.stringify(error.detail);
    throw new Error(detailMessage || "Failed to run command");
  }

  return await res.json();
}
