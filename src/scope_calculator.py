import json
import random
import requests
import logging
from typing import Union

from .config import alias_host_dict, host_alias_dict, injected_host_list
from .fault_injector import FaultInjector, alias_injector_dict
from .db import Database, alias_database_dict

class ScopeCalculator:

    @staticmethod
    def query_nodes() -> Union[list[str], list[str]]:
        '''返回leader的host（但用列表装着）以及所有节点的host'''
        try:
            host = list(alias_host_dict.values())[0]  # Any database
            api_port = list(alias_database_dict.values())[0].config.api_port
            status_query_url = f"http://{host}:{api_port}/status?pretty"
            
            response = requests.get(status_query_url)
            if response.status_code == 200:
                logging.debug("Query executed successfully.")
                node_data = response.json()
                data = response.json()
                leader_info = data["store"]["leader"]
                node_info = data["store"]["nodes"]
                leader_host: list[str] = [leader_info["addr"].split(":")[0]]  # 去掉端口
                node_host_list: list[str] = []
                for node in node_info:
                    node_host_list.append(node["addr"].split(":")[0])
                return leader_host, node_host_list
            else:
                raise Exception(str(response.text))
        except Exception as e:
            logging.error(f"Query node info failed: {e}")
            raise Exception(f"Query node info failed: {e}")
    
    @staticmethod
    def get_injectors_from_scope(scope: str) -> list[FaultInjector]:
        leader_host, node_host_list = ScopeCalculator.query_nodes()
        host_list = []
        try:
            if scope == "all_nodes":
                host_list = node_host_list
            elif scope == "half_nodes":
                host_list = random.sample(node_host_list, len(node_host_list) // 2 + 1)
            elif scope == "any_node":
                host_list = random.sample(node_host_list, 1)
            elif scope == "leader":
                host_list = leader_host
            elif scope == "all_followers":
                host_list = list(set(node_host_list) - set(leader_host))
            elif scope == "any_follower":
                follower_list = list(set(node_host_list) - set(leader_host))
                host_list = random.sample(follower_list, 1)
        except ValueError as e:
            logging.warn(f"The candidate list may be empty, please examine the scope you offer.")
             
        if len(host_list) == 0:
            logging.warn(f"The scope {scope} is empty, please examine the scope you offer.")
        injector_list: list[FaultInjector] = []
        for host in host_list:
            injector_list.append(alias_injector_dict[host_alias_dict[host]])
        return injector_list
    
    @staticmethod
    def get_databases_from_scope(scope: str) -> list[Database]:
        leader_host, node_host_list = ScopeCalculator.query_nodes()
        host_list = []
        try:
            if scope == "any_node":
                host_list = random.sample(node_host_list, 1)
            elif scope == "leader":
                host_list = leader_host
            elif scope == "any_follower":
                follower_list = list(set(node_host_list) - set(leader_host))
                host_list = random.sample(follower_list, 1)
            elif scope == "any_fault_injected_node":
                host_list = random.sample(injected_host_list, 1)
            elif scope == "fault_injected_leader":
                host_list = list(set(leader_host) & set(injected_host_list))
            elif scope == "any_fault_injected_follower":
                follower_list = list(set(node_host_list) - set(leader_host))
                host_list = list(set(follower_list) & set(injected_host_list))
        except ValueError as e:
            logging.warn(f"The candidate list may be empty, please examine the scope you offer.")
             
        if len(host_list) == 0:
            logging.warn(f"The scope {scope} is empty, please examine the scope you offer.")
        database_list: list[Database] = []
        for host in host_list:
            database_list.append(alias_database_dict[host_alias_dict[host]])
        return database_list