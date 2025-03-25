import json
import asyncio
import logging
from typing import Type
from abc import ABC, abstractmethod

from .fault_injector import FaultInjector
from .tools import time_string_to_seconds

class Nemesis(ABC):
    """所有故障注入的基类"""
    name: str
    nemesis_type: str
    nemesis_subtype: str
    target_scope: str
    start_time: int
    duration: str
    unique_id: dict[FaultInjector, list[str]] = {}
    
    def __init__(self, name: str, n_type: str, n_subtype: str, scope: str, start_time: str, duration: str):
        self.name = name
        self.type = n_type
        self.subtype = n_subtype
        self.scope = scope
        self.start_time = time_string_to_seconds(start_time)
        self.duration = duration
        
    def __str__(self):
        return f"{self.name} on {str(self.scope)} starts at {self.start_time} for {self.duration}"

    @abstractmethod
    def inject(self):
        """注入故障"""
        pass

    @abstractmethod
    def recover(self):
        """恢复故障"""
        pass
    
    def dispatch_inject_command(self, command):
        # 这里还有问题，要先把scope转成target_injectors
        for injector in self.target_injectors:
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


class NetworkNemesis(Nemesis):
    """所有网络故障的基类"""
    def __init__(self, name: str, subtype: str, scope: str, start_time: str, duration: str):
        super().__init__(name, "Network", subtype, scope, start_time, duration)


class NetworkLoss(NetworkNemesis):
    def __init__(self, scope: str, start_time: str, duration: str, percent: int = 100):
        super().__init__("Packet_Loss", "Loss", scope, start_time, duration)
        self.percent = percent

    async def inject(self):
        asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network loss --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --percent {self.percent}"
        self.dispatch_inject_command(command)
        
    def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkDelay(NetworkNemesis):
    def __init__(self, scope: str, start_time: str, duration: str, delay_time: int = 5):
        super().__init__("Network Delay", "Delay", scope, start_time, duration)
        self.delay_time = delay_time
        
    async def inject(self):
        asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network delay --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --time {self.delay_time}"
        self.dispatch_inject_command(command)

    def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkDuplicate(NetworkNemesis):
    def __init__(self, scope: str, start_time: str, duration: str, percent: int = 100):
        super().__init__("Packet Duplication", "Duplicate", scope, start_time, duration)
        self.percent = percent

    async def inject(self):
        asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network duplicate --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --percent {self.percent}"
        self.dispatch_inject_command(command)

    def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

class NetworkCorrupt(NetworkNemesis):
    def __init__(self, scope: str, start_time: str, duration: str, percent: int = 100):
        super().__init__("Packet Corruption", "Corrupt", scope, start_time, duration)
        self.percent = percent

    async def inject(self):
        asyncio.sleep(self.start_time)
        logging.info(f"Injecting {self}...")
        command = f"blade create network corrupt --interface eth0 --exclude-port 22,4001 --timeout {self.duration} --percent {self.percent}"
        self.dispatch_inject_command(command)

    def recover(self):
        logging.info(f"Recovering {self}...")
        self.dispatch_recover_command()
        

NEMESIS_MAPPING: dict[str, Type[Nemesis]] = {
    "network_loss": NetworkLoss,
    "network_delay": NetworkDelay,
    "network_duplicate": NetworkDuplicate,
    "network_corrupt": NetworkCorrupt
}

