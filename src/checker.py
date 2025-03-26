import json
import asyncio
from typing import Type
from abc import ABC, abstractmethod

from .db import Database
from .tools import time_string_to_seconds

class Check(ABC):
    """所有检查的基类"""
    name: str
    target_hosts: list[str]
    target_database: list[Database]
    start_time: int

    def __init__(self, name: str, hosts: list[str], database: list[Database], start_time: str):
        self.name = name
        self.target_hosts = hosts
        self.target_database = database
        self.start_time = time_string_to_seconds(start_time)
        
    @abstractmethod
    async def start(self):
        pass
    
    def query_sql(self, database: Database, sql: str):
        return database.query(sql)
        
    def __str__(self):
        return f"{self.name} on {str(self.target_hosts)} starts at {self.start_time}"
    

class IntegrityCheck(Check):
    def __init__(self, hosts, database, start_time):
        super().__init__("Integrity Check", hosts, database, start_time)
    
    async def start(self):
        await asyncio.sleep(self.start_time)
        sql = f"select * from tc ordered by count"
        output = self.query_sql(self.target_database[0], sql)
        # @todo：还未实现实质性的检查
        print(output)
        
        
CHECK_MAPPING: dict[str, Type[Check]] = {
    "integrity_check": IntegrityCheck
}