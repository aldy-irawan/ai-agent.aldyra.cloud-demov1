import requests
import json

ZABBIX_URL = "http://127.0.0.1/zabbix/api_jsonrpc.php"
ZABBIX_TOKEN = "794c15af0bfff42533988c6c892577ed845bbba5c539e3545e7dc108cee69558"


def zabbix_api(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "auth": ZABBIX_TOKEN,
        "id": 1
    }

    response = requests.post(
        ZABBIX_URL,
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    result = response.json()

    if "error" in result:
        raise Exception(result["error"])

    return result["result"]


# Get active problems
problems = zabbix_api(
    "problem.get",
    {
        "output": "extend",
        "sortfield": ["eventid"],
        "sortorder": "DESC",
        "limit": 10
    }
)


result = []

for problem in problems:

    trigger_id = problem["objectid"]

    triggers = zabbix_api(
        "trigger.get",
        {
            "triggerids": trigger_id,
            "output": [
                "triggerid",
                "description",
                "priority"
            ],
            "selectHosts": [
                "hostid",
                "host",
                "name"
            ]
        }
    )

    if not triggers:
        continue

    trigger = triggers[0]

    host_name = "Unknown"

    if trigger.get("hosts"):
        host_name = trigger["hosts"][0]["name"]

    severity_map = {
        "0": "Not classified",
        "1": "Information",
        "2": "Warning",
        "3": "Average",
        "4": "High",
        "5": "Disaster"
    }

    result.append({
        "event_id": problem["eventid"],
        "host": host_name,
        "problem": problem["name"],
        "severity": severity_map.get(
            problem["severity"],
            problem["severity"]
        ),
        "trigger_id": trigger_id
    })


print(json.dumps(result, indent=2))
