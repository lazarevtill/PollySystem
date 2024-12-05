from app.core.ssh_utils import run_command_on_machine

def check_and_install_docker(host, port, user, ssh_key, password):
    # Check if docker is installed
    check_cmd = "which docker"
    result = run_command_on_machine(host, port, user, check_cmd, ssh_key, password)
    if "docker" not in result:
        # run installation script
        install_script = open("scripts/docker_install_check.sh", "r").read()
        return run_command_on_machine(host, port, user, install_script, ssh_key, password)
    return "Docker already installed"

def run_docker_compose_command(host, port, user, command, ssh_key, password):
    # Assume docker-compose.yml present on the machine or handle it accordingly
    # For demonstration: run docker compose up/down from a fixed directory
    cmd = f"cd ~/ && docker compose {command}"
    return run_command_on_machine(host, port, user, cmd, ssh_key, password)
