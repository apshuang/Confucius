import logging
import paramiko

from .config import ChaosConfig

class FaultInjector:
    def __init__(self, config: ChaosConfig):
        self.config = config
        self.connection = None
        self.ssh_client = None

    def connect(self):
        logging.debug(f"Connecting to root at {self.config.host}...")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动接受主机密钥
            self.ssh_client.connect(self.config.host, port=self.config.ssh_port,
                                    username=self.config.chaos_username, password=self.config.chaos_password)
            logging.info(f"SSH connection to {self.config.host} has already established.")

        except Exception as e:
            logging.error(f"Failed to connect to SSH: {e}")
            raise

    def execute_command(self, command):
        for i in range(self.config.retry_count):
            try:
                # 需要保证这个指令不是持续的（如果是，那就需要使用nohup）
                stdin, stdout, stderr = self.ssh_client.exec_command(command)
                output = stdout.read().decode()
                error = stderr.read().decode()
                if error:
                    raise Exception(error)
                return output
            except Exception as e:
                logging.warn(f"Retrying to execute {command}: {e} for {i+1}/{self.config.retry_count}....")
        logging.error(f"[ERROR] Failed to execute {command} for {self.config.retry_count} times")    
        raise Exception(f"[ERROR] Failed to execute {command} for {self.config.retry_count} times")

    def close(self):
        if self.ssh_client:
            self.ssh_client.close()
            logging.info(f"[INFO] Connection to {self.host} has already closed.")
        
        
alias_injector_dict: dict[str, FaultInjector] = {}