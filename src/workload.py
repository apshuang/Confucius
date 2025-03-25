import json
import logging
import asyncio
from typing import Type
from abc import ABC, abstractmethod

from .db import Database
from .tools import time_string_to_seconds

count = 0

class Workload(ABC):
    """所有workload的基类"""
    name: str
    target_hosts: list[str]
    target_database: list[Database]
    start_time: int
    times: int
    
    def __init__(self, name: str, hosts: list[str], database: list[Database], start_time: str, times: int):
        self.name = name
        self.target_hosts = hosts
        self.target_database = database
        self.start_time = time_string_to_seconds(start_time)
        self.times = times
        
    @abstractmethod
    def start(self):
        pass
    
    def execute_sql(self, database: Database, sql: str):
        return database.execute(sql)
    
    def query_sql(self, database: Database, sql: str):
        return database.query(sql)
        
    def __str__(self):
        return f"{self.name} on {str(self.target_hosts)} starts at {self.start_time} for {self.times} times"
    

class SingleInsert(Workload):
    def __init__(self, hosts, database, start_time, times):
        super().__init__("Single Insert", hosts, database, start_time, times)
    
    async def start(self):
        asyncio.sleep(self.start_time)
        global count
        count += 1
        sql = f"insert into tc values('james', {count})"
        self.execute_sql(self.target_database[0], sql)
        
        
WORKLOAD_MAPPING: dict[str, Type[Workload]] = {
    "single_insert": SingleInsert
}