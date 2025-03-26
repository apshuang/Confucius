import requests
import json
import logging

url = "http://10.10.2.131:4001/db/execute?pretty&timings"
headers = {"Content-Type": "application/json"}
data  = [
    "CREATE TABLE IF NOT EXISTS tc (name TEXT, count int);", 
    "DELETE FROM tc;"
]
print(data)
response = requests.post(url, headers=headers, data=json.dumps(data))

print(response.status_code)
print(response.json())  # 如果返回的是 JSON 数据
