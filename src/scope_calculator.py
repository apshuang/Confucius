import json
import requests
import logging

from .config import alias_host_dict
from .fault_injector import FaultInjector, alias_injector_dict
from .db import Database

class ScopeCalculator:

    @staticmethod
    def query_nodes(host: str, api_port: int):
        api_url_base = f"{host}:{api_port}/db/"
        query_nodes_command = ".nodes"
        response = requests.post(f"{api_url_base}/query", data=json.dumps({"query": query_nodes_command}))
        print(response)
        if response.status_code == 200:
            logging.info("Query executed successfully.")
            return response.json()
        else:
            logging.error(f"Query failed: {response.text}")
            return None
    
    @staticmethod
    def get_hosts_from_scope(host: str, api_port: int, scope: str) -> list[FaultInjector]:
        ScopeCalculator.query_nodes(host, api_port)
        if scope == "all_follower":
            pass
        
        return []