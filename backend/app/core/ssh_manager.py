# app/core/ssh_manager.py
import os
import paramiko
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

class SSHManager:
    def __init__(self, ssh_dir="~/.ssh/pollysystem"):
        self.ssh_dir = os.path.expanduser(ssh_dir)
        Path(self.ssh_dir).mkdir(parents=True, exist_ok=True)
        self.private_key_path = os.path.join(self.ssh_dir, "id_rsa")
        self.public_key_path = os.path.join(self.ssh_dir, "id_rsa.pub")
        self._ensure_keys_exist()

    def _ensure_keys_exist(self):
        """Ensure SSH key pair exists, generate if it doesn't."""
        if not os.path.exists(self.private_key_path) or not os.path.exists(self.public_key_path):
            logger.info("Generating new SSH key pair...")
            self._generate_key_pair()
        else:
            # Validate existing keys
            try:
                paramiko.RSAKey.from_private_key_file(self.private_key_path)
            except Exception as e:
                logger.warning(f"Invalid existing SSH key, regenerating: {e}")
                self._generate_key_pair()

    def _generate_key_pair(self):
        """Generate a new RSA key pair."""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )

            # Generate private key in PEM format
            pem_private = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            # Generate public key in OpenSSH format
            public_key = private_key.public_key()
            pem_public = public_key.public_bytes(
                encoding=serialization.Encoding.OpenSSH,
                format=serialization.PublicFormat.OpenSSH
            )

            # Write private key
            with open(self.private_key_path, 'wb') as f:
                f.write(pem_private)
            os.chmod(self.private_key_path, 0o600)

            # Write public key
            with open(self.public_key_path, 'wb') as f:
                f.write(pem_public)
            os.chmod(self.public_key_path, 0o644)

            logger.info("Successfully generated new SSH key pair")

        except Exception as e:
            logger.error(f"Failed to generate SSH key pair: {e}")
            raise

    def get_public_key(self):
        """Get the public key content."""
        try:
            with open(self.public_key_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            logger.error(f"Failed to read public key: {e}")
            raise

    def deploy_key(self, host, port, user, password):
        """Deploy the public key to a remote host."""
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            logger.info(f"Connecting to {host} to deploy SSH key...")
            ssh.connect(
                hostname=host,
                port=port,
                username=user,
                password=password,
                timeout=10
            )

            public_key = self.get_public_key()
            commands = [
                "mkdir -p ~/.ssh",
                "chmod 700 ~/.ssh",
                f"echo '{public_key}' >> ~/.ssh/authorized_keys",
                "chmod 600 ~/.ssh/authorized_keys",
                "sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"
            ]

            for cmd in commands:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                if exit_status != 0:
                    error = stderr.read().decode().strip()
                    raise Exception(f"Command failed: {error}")

            logger.info(f"Successfully deployed SSH key to {host}")
            return True

        except Exception as e:
            logger.error(f"Failed to deploy SSH key to {host}: {e}")
            raise

        finally:
            ssh.close()

ssh_manager = SSHManager()

# Test the SSH key generation on import
try:
    ssh_manager._ensure_keys_exist()
except Exception as e:
    logger.error(f"Failed to initialize SSH manager: {e}")
    raise