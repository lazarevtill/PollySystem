# app/core/metrics_utils.py
from app.core.ssh_utils import run_command_on_machine, SSHConnectionError
import logging

logger = logging.getLogger(__name__)

class MetricsCollectionError(Exception):
    pass

def get_machine_metrics(host: str, port: int, user: str, ssh_key: str = None, password: str = None):
    """Get CPU and memory metrics from a remote machine."""
    try:
        # Simpler, more reliable commands
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' || echo '0.0'"
        mem_cmd = "free -m | awk 'NR==2{printf \"%d,%d\", $3,$2}' || echo '0,1'"
        
        try:
            cpu_usage_str = run_command_on_machine(host, port, user, cpu_cmd, ssh_key, password)
            cpu_usage = float(cpu_usage_str) if cpu_usage_str.strip() else 0.0
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to parse CPU metrics for {host}: {str(e)}")
            cpu_usage = 0.0

        try:
            mem_usage_str = run_command_on_machine(host, port, user, mem_cmd, ssh_key, password)
            used_mem, total_mem = map(int, mem_usage_str.split(",")) if "," in mem_usage_str else (0, 1)
        except (ValueError, AttributeError) as e:
            logger.warning(f"Failed to parse memory metrics for {host}: {str(e)}")
            used_mem, total_mem = 0, 1

        return {
            "cpu_usage_percent": round(cpu_usage, 2),
            "memory_used_mb": used_mem,
            "memory_total_mb": total_mem,
            "status": "ok"
        }

    except SSHConnectionError as e:
        logger.error(f"SSH connection error for {host}: {str(e)}")
        return {
            "cpu_usage_percent": 0.0,
            "memory_used_mb": 0,
            "memory_total_mb": 1,
            "status": "error",
            "error": f"Connection failed: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Failed to collect metrics for {host}: {str(e)}")
        return {
            "cpu_usage_percent": 0.0,
            "memory_used_mb": 0,
            "memory_total_mb": 1,
            "status": "error",
            "error": f"Failed to collect metrics: {str(e)}"
        }