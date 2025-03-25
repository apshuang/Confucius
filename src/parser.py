import yaml
from typing import Any

from .config import DatabaseConfig, ChaosConfig
from .nemesis import *
from .workload import *
from .checker import *
from .tools import time_string_to_seconds
    
    
class YamlParser:
    cluster_size: int
    nodes: dict[str, str]
    retry_count: int
    
    def __init__(self, yaml_path):
        with open(yaml_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            self.cluster_size = config["cluster_size"]
            self.nodes = config["nodes"]
            self.retry_count = config["retry_count"]
    
    def get_nodes_name_list(self) -> list[str]:
        return list(self.nodes.keys())
    
    def get_database_config(self, node_name: str) -> DatabaseConfig:
        node_info = self.nodes[node_name]
        return DatabaseConfig(node_name, node_info["host"], node_info["api_port"], node_info["ssh_port"], 
                               node_info["db_username"], node_info["db_password"], self.retry_count)
        
    def get_chaos_config(self, node_name: str) -> ChaosConfig:
        node_info = self.nodes[node_name]
        return ChaosConfig(node_name, node_info["host"], node_info["ssh_port"], 
                           node_info["chaos_username"], node_info["chaos_password"], self.retry_count)
        

class PlanParser:
    description: str
    total_time: int
    event_list: list
    
    def __init__(self, plan_data):
        self.description = plan_data["thought"]
        self.total_time = time_string_to_seconds(plan_data["total_time"])
        self.event_list = self.parse_events(plan_data["events"])
    
    
    @staticmethod
    def parse_nemesis(nemesis_info: dict[str, Any]) -> Nemesis:
        title = nemesis_info.get("title")
        NemesisClass = NEMESIS_MAPPING.get(title)
        if NemesisClass is None:
            raise ValueError(f"Unknown nemesis type: {title}")
        
        return NemesisClass(
            scope=nemesis_info.get("scope", "none"),
            start_time=nemesis_info.get("start_time", "0s"),
            duration=nemesis_info.get("duration", "0s")
        )
        
    @staticmethod
    def parse_workload(workload_info: dict[str, Any]) -> Workload:
        title = workload_info.get("title")
        WorkloadClass = WORKLOAD_MAPPING.get(title)
        if WorkloadClass is None:
            raise ValueError(f"Unknown workload type: {title}")
        
        return Workload(
            scope=workload_info.get("scope", "none"),
            start_time=workload_info.get("start_time", "0s"),
            times=workload_info.get("times", "0")
        )
        
        
    @staticmethod
    def parse_checking(check_info: dict[str, Any]) -> Check:
        title = check_info.get("title")
        CheckClass = CHECK_MAPPING.get(title)
        if CheckClass is None:
            raise ValueError(f"Unknown checker type: {title}")
        
        return Workload(
            start_time=check_info.get("start_time", "0s"),
            times=check_info.get("times", "0")
        )

    @staticmethod
    def parse_events(event_list: list):
        event_object_list: list = []
        for event in event_list:
            if event["type"] == "nemesis":
                event_object_list.append(PlanParser.parse_nemesis(event))
            elif event["type"] == "workload":
                event_object_list.append(PlanParser.parse_workload(event))
            elif event["type"] == "check":
                event_object_list.append(PlanParser.parse_checking(event))
        return event_object_list