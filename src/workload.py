import json
import logging
import asyncio
from typing import Type
from abc import ABC, abstractmethod

from .db import Database
from .tools import time_string_to_seconds, seconds_to_time_string
from .scope_calculator import ScopeCalculator

count = 0

class Workload(ABC):
    """所有workload的基类"""
    name: str
    target_scope: str
    start_time: int
    times: int
    
    def __init__(self, name: str, scope: str, start_time: str, times: int):
        self.name = name
        self.target_scope = scope
        self.start_time = time_string_to_seconds(start_time)
        self.times = times
        
    @abstractmethod
    async def start(self):
        pass
    
    def execute_sql(self, sql: str):
        target_databases = ScopeCalculator.get_databases_from_scope(self.target_scope)
        for database in target_databases:
            database.execute(sql)
    
    def query_sql(self, sql: str):
        target_databases = ScopeCalculator.get_databases_from_scope(self.target_scope)
        for database in target_databases:
            database.query(sql)
        
    def __str__(self):
        return f"{self.name} on {str(self.target_hosts)} starts at {seconds_to_time_string(self.start_time)} for {self.times} times"
    

class SingleInsert(Workload):
    def __init__(self, scope, start_time, times):
        super().__init__("Single Insert", scope, start_time, times)
    
    async def start(self):
        await asyncio.sleep(self.start_time)
        global count
        count += 1
        sql = [f'INSERT INTO tc VALUES("james", {count})']
        self.execute_sql(sql)
        
        
WORKLOAD_MAPPING: dict[str, Type[Workload]] = {
    "single_insert": SingleInsert
}