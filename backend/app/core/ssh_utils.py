# app/core/ssh_utils.py
import paramiko
import socket
import os
import io
import logging
import tempfile
from contextlib import contextmanager
from typing import Optional, Union, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class SSHConnectionError(Exception):
    pass

class SSHKeyError(Exception):
    pass

def normalize_key_content(key_content: str) -> str:
    """Normalize SSH key content by fixing line endings and format."""
    # Remove any carriage returns and normalize to Unix line endings
    key_content = key_content.replace('\r\n', '\n').replace('\r', '\n')
    lines = key_content.strip().split('\n')
    
    # Check if this is an OpenSSH format key
    if not any(line.startswith('-----BEGIN ') for line in lines):
        return key_content

    # Properly format OpenSSH key
    formatted_lines = []
    in_body = False
    last_was_header = False

    for line in lines:
        if line.startswith('-----BEGIN '):
            formatted_lines.append(line)
            in_body = True
            last_was_header = True
        elif line.startswith('-----END '):
            if not formatted_lines[-1] == '':
                formatted_lines.append('')
            formatted_lines.append(line)
            in_body = False
        elif in_body:
            if last_was_header:
                formatted_lines.append('')
                last_was_header = False
            formatted_lines.append(line)

    return '\n'.join(formatted_lines)

def detect_key_type(key_content: str) -> str:
    """Detect the type of SSH key from its content."""
    normalized = normalize_key_content(key_content)
    
    if "OPENSSH PRIVATE KEY" in normalized:
        return "openssh"
    elif "RSA PRIVATE KEY" in normalized:
        return "rsa"
    elif "DSA PRIVATE KEY" in normalized:
        return "dsa"
    elif "EC PRIVATE KEY" in normalized:
        return "ecdsa"
    elif "PRIVATE KEY" in normalized:  # Generic key format
        return "generic"
    else:
        return "unknown"

@contextmanager
def create_temp_key_file(key_content: str):
    """Create a temporary file with SSH key content."""
    temp_file = None
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write(normalize_key_content(key_content))
        temp_file.flush()
        os.chmod(temp_file.name, 0o600)
        yield temp_file.name
    finally:
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception as e:
                logger.warning(f"Failed to remove temporary key file: {e}")

def load_ssh_key(key_path_or_content: str, passphrase: Optional[str] = None) -> Any:
    """
    Load an SSH key from a file path or content string.
    Supports RSA, DSA, ECDSA, Ed25519, and OpenSSH key formats.
    """
    key_content = key_path_or_content
    if os.path.exists(key_path_or_content):
        with open(key_path_or_content, 'r') as f:
            key_content = f.read()

    # Normalize the key content
    key_content = normalize_key_content(key_content)
    key_type = detect_key_type(key_content)
    logger.debug(f"Detected key type: {key_type}")

    # Map of key types to their respective paramiko classes and names
    key_handlers = [
        (paramiko.RSAKey, "RSA", lambda: paramiko.RSAKey.from_private_key),
        (paramiko.DSSKey, "DSS", lambda: paramiko.DSSKey.from_private_key),
        (paramiko.ECDSAKey, "ECDSA", lambda: paramiko.ECDSAKey.from_private_key),
        (paramiko.Ed25519Key, "Ed25519", lambda: paramiko.Ed25519Key.from_private_key)
    ]

    errors = []
    # Try loading with StringIO first (memory-based)
    for key_class, key_name, key_loader in key_handlers:
        try:
            key_file = io.StringIO(key_content)
            if passphrase:
                key = key_loader()(key_file, password=passphrase)
            else:
                try:
                    key = key_loader()(key_file)
                except paramiko.ssh_exception.PasswordRequiredException:
                    errors.append(f"{key_name}: Key is encrypted and requires a passphrase")
                    continue
            logger.info(f"Successfully loaded {key_name} key from content")
            return key
        except Exception as e:
            errors.append(f"{key_name} (memory): {str(e)}")

    # If memory loading fails, try with temporary file
    with create_temp_key_file(key_content) as temp_path:
        for key_class, key_name, key_loader in key_handlers:
            try:
                if passphrase:
                    key = key_class.from_private_key_file(temp_path, password=passphrase)
                else:
                    try:
                        key = key_class.from_private_key_file(temp_path)
                    except paramiko.ssh_exception.PasswordRequiredException:
                        errors.append(f"{key_name}: Key is encrypted and requires a passphrase")
                        continue
                logger.info(f"Successfully loaded {key_name} key from file")
                return key
            except Exception as e:
                errors.append(f"{key_name} (file): {str(e)}")

    error_msg = f"Failed to load SSH key (type: {key_type}). Errors: " + '; '.join(errors)
    logger.error(error_msg)
    raise SSHKeyError(error_msg)

@contextmanager
def ssh_connection(
    host: str,
    port: int,
    username: str,
    ssh_key: Optional[str] = None,
    password: Optional[str] = None,
    key_passphrase: Optional[str] = None,
    timeout: int = 10
):
    """Create an SSH connection with comprehensive error handling."""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        if ssh_key:
            try:
                pkey = load_ssh_key(ssh_key, key_passphrase)
                ssh.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    pkey=pkey,
                    timeout=timeout,
                    look_for_keys=False
                )
            except Exception as e:
                raise SSHConnectionError(f"Failed to connect with SSH key: {str(e)}")
        else:
            try:
                ssh.connect(
                    hostname=host,
                    port=port,
                    username=username,
                    password=password,
                    timeout=timeout,
                    look_for_keys=False
                )
            except Exception as e:
                raise SSHConnectionError(f"Failed to connect with password: {str(e)}")
            
        yield ssh
        
    except socket.timeout:
        raise SSHConnectionError(f"Connection timed out while connecting to {host}")
    except paramiko.AuthenticationException:
        raise SSHConnectionError(
            f"Authentication failed for {username}@{host}. " 
            f"{'Key is invalid or encrypted' if ssh_key else 'Invalid password'}"
        )
    except Exception as e:
        raise SSHConnectionError(f"Failed to connect to {host}: {str(e)}")
    finally:
        ssh.close()

def run_command_on_machine(
    host: str,
    port: int,
    user: str,
    command: str,
    ssh_key: Optional[str] = None,
    password: Optional[str] = None,
    key_passphrase: Optional[str] = None,
    timeout: int = 10
) -> str:
    """Execute a command on a remote machine via SSH with comprehensive error handling."""
    try:
        with ssh_connection(
            host, port, user, ssh_key, password, key_passphrase, timeout
        ) as ssh:
            # Set up the channel with proper handling
            transport = ssh.get_transport()
            if not transport:
                raise SSHConnectionError("Failed to establish SSH transport")
            
            # Open channel and set timeout
            channel = transport.open_session()
            channel.settimeout(timeout)
            
            # Execute command
            channel.exec_command(command)
            
            # Read output and error streams
            stdout = channel.makefile('r')
            stderr = channel.makefile_stderr('r')
            
            # Get output and error content
            output = stdout.read().strip()
            error = stderr.read().strip()
            
            # Get exit status
            exit_status = channel.recv_exit_status()
            
            if exit_status != 0:
                error_msg = error if error else f"Command exited with status {exit_status}"
                raise SSHConnectionError(f"Command failed: {error_msg}")
            
            return output.decode('utf-8') if isinstance(output, bytes) else output
            
    except SSHConnectionError:
        raise
    except Exception as e:
        logger.error(f"Failed to execute command on {host}: {str(e)}")
        raise SSHConnectionError(str(e))

class SSHKeyManager:
    """Manage SSH keys, including generation and deployment."""
    
    def __init__(self, ssh_dir: str = "~/.ssh/pollysystem"):
        self.ssh_dir = os.path.expanduser(ssh_dir)
        self.private_key_path = os.path.join(self.ssh_dir, "id_rsa")
        self.public_key_path = os.path.join(self.ssh_dir, "id_rsa.pub")
        self._ensure_ssh_dir()

    def _ensure_ssh_dir(self):
        """Ensure SSH directory exists with proper permissions."""
        os.makedirs(self.ssh_dir, mode=0o700, exist_ok=True)

    def generate_key_pair(self, key_type: str = "rsa", bits: int = 2048):
        """Generate a new SSH key pair."""
        if key_type.lower() == "rsa":
            key = paramiko.RSAKey.generate(bits)
        elif key_type.lower() == "dsa":
            key = paramiko.DSSKey.generate(bits)
        elif key_type.lower() == "ecdsa":
            key = paramiko.ECDSAKey.generate()
        else:
            raise ValueError(f"Unsupported key type: {key_type}")

        # Save private key
        key.write_private_key_file(self.private_key_path)
        os.chmod(self.private_key_path, 0o600)

        # Save public key
        with open(self.public_key_path, 'w') as f:
            f.write(f"{key.get_name()} {key.get_base64()} pollysystem\n")
        os.chmod(self.public_key_path, 0o644)

    def deploy_key(self, host: str, port: int, user: str, password: str) -> bool:
        """Deploy public key to remote host."""
        if not os.path.exists(self.public_key_path):
            self.generate_key_pair()

        with open(self.public_key_path, 'r') as f:
            public_key = f.read().strip()

        try:
            with ssh_connection(host, port, user, password=password) as ssh:
                commands = [
                    "mkdir -p ~/.ssh",
                    "chmod 700 ~/.ssh",
                    f"echo '{public_key}' >> ~/.ssh/authorized_keys",
                    "chmod 600 ~/.ssh/authorized_keys",
                    "sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"
                ]

                for cmd in commands:
                    stdin, stdout, stderr = ssh.exec_command(cmd)
                    if stderr.read():
                        raise SSHConnectionError(f"Failed to execute: {cmd}")

                return True

        except Exception as e:
            raise SSHConnectionError(f"Failed to deploy key: {str(e)}")

ssh_manager = SSHKeyManager()