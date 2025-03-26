import json
import logging
import asyncio
from typing import Type
from abc import ABC, abstractmethod

from .db import Database, alias_database_dict
from .tools import time_string_to_seconds

class Check(ABC):
    """所有检查的基类"""
    name: str
    start_time: int

    def __init__(self, name: str, start_time: str):
        self.name = name
        self.start_time = time_string_to_seconds(start_time)
        
    @abstractmethod
    async def start(self):
        pass
    
    async def query_sql(self, sql: str):
        database = list(alias_database_dict.values())[0]
        return await database.query(sql)
        
    def __str__(self):
        return f"{self.name} on {str(self.target_hosts)} starts at {self.start_time}"
    

class IntegrityCheck(Check):
    def __init__(self, start_time):
        super().__init__("Integrity Check", start_time)
    
    async def start(self) -> bool:
        await asyncio.sleep(self.start_time)
        sql = [f"select * from tc order by count"]
        output = await self.query_sql(sql)
        print(output)
        values = (output[0]).get("values")
        if values is None:
            return True
        for i in range(len(values) - 1):
            if values[i][1] + 1 != values[i+1][1]:
                return True
        logging.info("Integrity check passed!")
        return False
        
        
CHECK_MAPPING: dict[str, Type[Check]] = {
    "integrity_check": IntegrityCheck
}