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
    
    def init_table_tc(self):
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

    def teardownDB(self):
        if self.ssh_client is None:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 自动接受主机密钥
            self.ssh_client.connect(self.config.host, port=self.config.ssh_port,
                                    username=self.config.db_username, password=self.config.db_password)
            
        try:
            close_db_command = "bash /home/centos/kill_old_db_connect.sh"
            stdin, stdout, stderr = self.ssh_client.exec_command(close_db_command)
            error = stderr.read().decode()
            if error:
                raise Exception(error)
            self.ssh_client.close()
            logging.info(f"SSH connection to database node {self.config.host} has already closed. SSH connection is closed.")
        except Exception as e:
            logging.error(f"Error closing database at {self.config.host}: {e}")
        

    def execute(self, sql: list[str]) -> bool:
        for i in range(self.config.retry_count):
            try:
                logging.debug(f"Executing SQL query: {sql}")
                url = f"{self.api_url_base}/execute?pretty&timings"
                response = requests.post(url, json=sql, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    results = (response.json()).get("results")
                    for result_info in results:
                        # 如果这里包含多语句的话，是不是还需要有一些rollback？
                        if result_info.get("error"):
                            return False
                    logging.info(f"Query {sql} executed successfully.")
                    return True
                else:
                    raise Exception(f"Status_code: {response.status_code}, error: {response.text}")
            except Exception as e:
                logging.warning(f"Retrying to execute {sql}: {e} for {i+1}/{self.config.retry_count}....")
        logging.error(f"[ERROR] Failed to execute {sql} for {self.config.retry_count} times")    
        raise Exception(f"[ERROR] Failed to execute {sql} for {self.config.retry_count} times")
        
    def query(self, sql: list[str]):
        for i in range(self.config.retry_count):
            try:
                logging.debug(f"Querying SQL query: {sql}")
                url = f"{self.api_url_base}/query?pretty&timings"
                response = requests.post(url, json=sql, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    logging.info(f"Query {sql} successfully.")
                    return (response.json()).get("results")
                else:
                    raise Exception(f"Status_code: {response.status_code}, error: {response.text}")
            except Exception as e:
                logging.warning(f"Retrying to query {sql} for {i+1}/{self.config.retry_count}....")
        logging.error(f"[ERROR] Failed to query {sql} for {self.config.retry_count} times")    
        raise Exception(f"[ERROR] Failed to query {sql} for {self.config.retry_count} times")
        

alias_database_dict: dict[str, Database] = {}