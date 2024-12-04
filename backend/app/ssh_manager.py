import paramiko
import tempfile
from pathlib import Path
from cryptography.fernet import Fernet
from contextlib import contextmanager
import logging
from typing import Tuple, Optional
import os

logger = logging.getLogger(__name__)

class SSHManager:
    def __init__(self, encryption_key: str):
        """Initialize SSH Manager with encryption key for storing private keys"""
        self.fernet = Fernet(encryption_key.encode() if isinstance(encryption_key, str) else encryption_key)
    
    def generate_ssh_key_pair(self) -> Tuple[str, str]:
        """Generate new SSH key pair"""
        try:
            key = paramiko.RSAKey.generate(4096)
            pkey_file = tempfile.NamedTemporaryFile(delete=False)
            pub_file = tempfile.NamedTemporaryFile(delete=False)
            
            try:
                # Save private key
                key.write_private_key(pkey_file)
                pkey_file.seek(0)
                private_key = pkey_file.read().decode()
                
                # Generate public key
                public_key = f"{key.get_name()} {key.get_base64()} auto-generated"
                pub_file.write(public_key.encode())
                pub_file.seek(0)
                
                return private_key, public_key
            finally:
                pkey_file.close()
                pub_file.close()
                os.unlink(pkey_file.name)
                os.unlink(pub_file.name)
                
        except Exception as e:
            logger.error(f"Failed to generate SSH key pair: {str(e)}")
            raise
    
    def encrypt_private_key(self, private_key: str) -> bytes:
        """Encrypt private key for storage"""
        try:
            return self.fernet.encrypt(private_key.encode())
        except Exception as e:
            logger.error(f"Failed to encrypt private key: {str(e)}")
            raise
    
    def decrypt_private_key(self, encrypted_key: bytes) -> str:
        """Decrypt private key for use"""
        try:
            return self.fernet.decrypt(encrypted_key).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt private key: {str(e)}")
            raise
    
    @contextmanager
    def get_ssh_client(self, hostname: str, username: str, private_key: bytes, port: int = 22):
        """Context manager for SSH connections"""
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Create temporary private key file
        with tempfile.NamedTemporaryFile(mode='w') as key_file:
            try:
                # Write decrypted private key to temporary file
                key_file.write(self.decrypt_private_key(private_key))
                key_file.flush()
                
                # Connect to remote host
                client.connect(
                    hostname=hostname,
                    username=username,
                    key_filename=key_file.name,
                    port=port,
                    timeout=10
                )
                yield client
            except Exception as e:
                logger.error(f"SSH connection failed: {str(e)}")
                raise
            finally:
                client.close()

    def execute_command(self, client: paramiko.SSHClient, command: str, timeout: int = 60) -> Tuple[str, str]:
        """Execute command and return stdout and stderr"""
        try:
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            return stdout.read().decode(), stderr.read().decode()
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            raise

    def copy_file(self, client: paramiko.SSHClient, local_path: str, remote_path: str):
        """Copy local file to remote host"""
        try:
            sftp = client.open_sftp()
            try:
                sftp.put(local_path, remote_path)
            finally:
                sftp.close()
        except Exception as e:
            logger.error(f"File copy failed: {str(e)}")
            raise
