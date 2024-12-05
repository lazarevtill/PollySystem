import paramiko

def run_command_on_machine(host, port, user, command, ssh_key=None, password=None):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if ssh_key:
        key = paramiko.RSAKey.from_private_key_file(ssh_key)
        ssh.connect(hostname=host, port=port, username=user, pkey=key, look_for_keys=False)
    else:
        ssh.connect(hostname=host, port=port, username=user, password=password, look_for_keys=False)
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()
    ssh.close()
    if error:
        return f"Error: {error}"
    return output
