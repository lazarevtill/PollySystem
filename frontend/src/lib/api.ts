export async function getMachines() {
    const res = await fetch('http://localhost:8000/api/v1/machines');
    return await res.json();
  }
  
  export async function getMachineMetrics(host: string) {
    const res = await fetch(`http://localhost:8000/api/v1/machines/${host}/metrics`);
    if (!res.ok) throw new Error("Failed to fetch metrics");
    return await res.json();
  }
  
  export async function addMachine(data: { name: string, host: string, user: string, password?: string }) {
    const res = await fetch('http://localhost:8000/api/v1/machines', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Failed to add machine");
    return await res.json();
  }
  
  export async function deleteMachine(host: string) {
    const res = await fetch(`http://localhost:8000/api/v1/machines/${host}`, { method: 'DELETE' });
    if (!res.ok) throw new Error("Failed to delete machine");
    return await res.json();
  }
  
  export async function runCommandAll(command: string) {
    const res = await fetch('http://localhost:8000/api/v1/commands/run_all', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ command })
    });
    if (!res.ok) throw new Error("Failed to run command");
    return await res.json();
  }
  