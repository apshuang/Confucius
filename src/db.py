import json
import requests
import paramiko
import logging
from threading import Thread

from .config import DatabaseConfig


class Database:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.ssh_client = None
        self.api_url_base = f"http://{config.host}:{self.config.api_port}/db"

    def setupDB(self):
        logging.debug(f"Connecting to rqlite database at {self.config.host}...")
        
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动接受主机密钥
            self.ssh_client.connect(self.config.host, port=self.config.ssh_port,
                                    username=self.config.db_username, password=self.config.db_password)
            start_db_command = "bash /home/centos/start_db.sh"
            stdin, stdout, stderr = self.ssh_client.exec_command(start_db_command)
            error = stderr.read().decode()
            if error:
                raise Exception(error)
            logging.info(f"SSH connection to {self.config.host} has established. Database is activated.")
        except Exception as e:
            logging.error(f"[ERROR] Failed to execute start_db command: {e}")
    
    def init_table(self):
        try:
            # 此处的语句可以做一些调整，甚至不必一定要用这一套方法来init
            create_table_sql = [
                "CREATE TABLE IF NOT EXISTS tc (name TEXT, count int);", 
                "DELETE FROM tc;"
                ]
            self.execute(create_table_sql)
            logging.info(f"Init database and create table tc successfully.")
        except Exception as e:
            logging.error(f"Failed to connect to SSH or setup database: {e}")
            raise

    def teardownDB(self): # 下面加上close_old_db_connect的调用
        if self.ssh_client:
            try:
                self.ssh_client.close()
                logging.info(f"SSH connection to database node {self.config.host} has already closed.")
            except Exception as e:
                logging.error(f"Error closing SSH connection: {e}")
        

    def execute(self, sql: list[str]):
        # @todo：这里还需要加上重试
        logging.debug(f"Executing SQL query: {sql}")
        response = requests.post(f"{self.api_url_base}/execute", json=json.dumps(sql), headers={"Content-Type": "application/json"})
        print(response)
        if response.status_code == 200:
            logging.info(f"Query {sql} executed successfully.")
            return response.json()
        else:
            logging.error(f"Query failed: {response.text}")
            return None
        
    def query(self, sql: list[str]):
        logging.debug(f"Querying SQL query: {sql}")
        response = requests.post(f"{self.api_url_base}/query", json=json.dumps(sql), headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            logging.info(f"Query {sql} executed successfully.")
            return response.json()
        else:
            logging.error(f"Query failed: {response.text}")
            return None
        

alias_database_dict: dict[str, Database] = {}