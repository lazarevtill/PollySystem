from app.core.ssh_utils import run_command_on_machine

def get_machine_metrics(host, port, user, ssh_key, password):
    # Example using top/free for CPU and Mem:
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}'"
    mem_cmd = "free -m | awk 'NR==2{printf \"%s,%s\", $3,$2}'"
    cpu_usage_str = run_command_on_machine(host, port, user, cpu_cmd, ssh_key, password)
    mem_usage_str = run_command_on_machine(host, port, user, mem_cmd, ssh_key, password)
    try:
        cpu_usage = float(cpu_usage_str)
    except ValueError:
        cpu_usage = 0.0
    used_mem, total_mem = mem_usage_str.split(",") if "," in mem_usage_str else (0, 1)
    return {
        "cpu_usage_percent": cpu_usage,
        "memory_used_mb": int(used_mem),
        "memory_total_mb": int(total_mem)
    }
