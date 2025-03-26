import json
import asyncio
import logging
from typing import Type
from abc import ABC, abstractmethod

from .fault_injector import FaultInjector
from .tools import time_string_to_seconds, seconds_to_time_string
from .scope_calculator import ScopeCalculator

class Nemesis(ABC):
    """所有故障注入的基类"""
    name: str
    nemesis_type: str
    nemesis_subtype: str
    target_scope: str
    start_time: int
    duration: int
    unique_id: dict[FaultInjector, list[str]] = {}
    
    def __init__(self, name: str, n_type: str, n_subtype: str, scope: str, start_time: str, duration: str):
        self.name = name
        self.type = n_type
        self.subtype = n_subtype
        self.scope = scope
        self.start_time = time_string_to_seconds(start_time)
        self.duration = time_string_to_seconds(duration)
        
    def __str__(self):
        return f"{self.name} on {str(self.scope)} starts at {seconds_to_time_string(self.start_time)}s for {self.duration}s"

    @abstractmethod
    async def inject(self):
        """注入故障"""
        pass

    @abstractmethod
    async def recover(self):
        # @todo: 这里还有问题，应该怎么去除那些injected_host
        """恢复故障"""
        pass
    
    def dispatch_inject_command(self, command):
        target_injectors = ScopeCalculator.get_injectors_from_scope(self.target_scope)
        for injector in target_injectors:
            output = injector.execute_command(command)
            output_dict = json.loads(output)
            if output_dict.get("code", 0) != 200 or not output_dict.get("success", False):
                logging.error(f"Inject nemesis failed on {injector.config.host}")
                raise Exception(f"Inject nemesis failed on {injector.config.host}")
            self.unique_id.setdefault(injector, [])
            self.unique_id[injector].append(output_dict["result"])
            
    def dispatch_recover_command(self):
        for injector, uid_list in self.unique_id.items():
            for uid in uid_list:
                output = injector.execute_command(f"blade destroy {uid}")
                output_dict = json.loads(output)
                if output_dict.get("code", 0) != 200 or not output_dict.get("success", False):
                    logging.error(f"Recover nemesis failed on {injector.config.host}")
                    raise Exception(f"Recover nemesis failed on {injector.config.host}")
        self.unique_id = {}
            
    def get_json_str(self):
        info_dict = {
            "title": f"{self.nemesis_type}_{self.nemesis_subtype}",
            "type": "nemesis",
            "description": self.name,
            "start_time": self.start_time,
            "duration": self.duration,
        }
        return json.dumps(info_dict)


class NetworkLoss(Nemesis):
    def __init__(self, scope: str, start_time: str, duration: str, percent: int):
        super().__init__("Packet_Loss", "Network", "Loss", scope, start_time, duration)
        self.percent = percent

    async def inject(self):
        await asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network loss --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --percent {self.percent}"
        self.dispatch_inject_command(command)
        
    async def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkDelay(Nemesis):
    def __init__(self, scope: str, start_time: str, duration: str, delay_time: int):
        super().__init__("Network Delay", "Network", "Delay", scope, start_time, duration)
        self.delay_time = delay_time
        
    async def inject(self):
        await asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network delay --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --time {self.delay_time}"
        self.dispatch_inject_command(command)

    async def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkDuplicate(Nemesis):
    def __init__(self, scope: str, start_time: str, duration: str, percent: int):
        super().__init__("Packet Duplication", "Network", "Duplicate", scope, start_time, duration)
        self.percent = percent

    async def inject(self):
        await asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network duplicate --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --percent {self.percent}"
        self.dispatch_inject_command(command)

    async def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkCorrupt(Nemesis):
    def __init__(self, scope: str, start_time: str, duration: str, percent: int):
        super().__init__("Packet Corruption", "Network", "Corrupt", scope, start_time, duration)
        self.percent = percent

    async def inject(self):
        await asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network corrupt --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --percent {self.percent}"
        self.dispatch_inject_command(command)

    async def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkNemesisFactory:
    @classmethod
    def create_network_nemesis(cls, data) -> Nemesis:
        title = data.get("title")
        parameters = data.get("parameters", {})
        if title == "network_loss":
            percent = parameters.get("percent", 100)
            return NetworkLoss(
                scope=data["scope"],
                start_time=data["start_time"],
                duration=data["duration"],
                percent=percent
            )
        elif title == "network_delay":
            delay_time = parameters.get("delay_time", 0)
            return NetworkDelay(
                scope=data["scope"],
                start_time=data["start_time"],
                duration=data["duration"],
                delay_time=delay_time
            )
        elif title == "network_duplicate":
            percent = parameters.get("percent", 100)
            return NetworkDuplicate(
                scope=data["scope"],
                start_time=data["start_time"],
                duration=data["duration"],
                percent=percent
            )
        elif title == "network_corrupt":
            percent = parameters.get("percent", 100)
            return NetworkDuplicate(
                scope=data["scope"],
                start_time=data["start_time"],
                duration=data["duration"],
                percent=percent
            )
        else:
            raise ValueError(f"Unknown nemesis type: {title}")

