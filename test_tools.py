from zabbix_tools import get_memory_usage
import json


memory = get_memory_usage("APP01")

print(json.dumps(memory, indent=2))
