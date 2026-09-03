import os
import requests

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

ZABBIX_URL = os.environ["ZABBIX_URL"]
ZABBIX_TOKEN = os.environ["ZABBIX_TOKEN"]


# ============================================================
# ZABBIX API
# ============================================================

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

        raise Exception(
            result["error"]
        )


    return result["result"]


# ============================================================
# GET ALL MONITORED HOSTS
# ============================================================

def get_all_hosts():

    hosts = zabbix_api(
        "host.get",
        {
            "output": [
                "hostid",
                "host",
                "name",
                "status"
            ],
            "filter": {
                "status": "0"
            },
            "sortfield": "name"
        }
    )


    result = []


    for host in hosts:

        result.append(
            {
                "hostid":
                    host["hostid"],

                "host":
                    host["host"],

                "name":
                    host["name"],

                "status":
                    host["status"]
            }
        )


    return result


# ============================================================
# GET ACTIVE PROBLEMS
# ============================================================

def get_active_problems():

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


    severity_map = {
        "0": "Not classified",
        "1": "Information",
        "2": "Warning",
        "3": "Average",
        "4": "High",
        "5": "Disaster"
    }


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

            host_name = \
                trigger["hosts"][0]["name"]


        result.append(
            {
                "event_id":
                    problem["eventid"],

                "host":
                    host_name,

                "problem":
                    problem["name"],

                "severity":
                    severity_map.get(
                        problem["severity"],
                        problem["severity"]
                    ),

                "trigger_id":
                    trigger_id
            }
        )


    return result


# ============================================================
# GET CPU USAGE
# ============================================================

def get_cpu_usage(host_name):

    # --------------------------------------------------------
    # Find host
    # --------------------------------------------------------

    hosts = zabbix_api(
        "host.get",
        {
            "filter": {
                "host": [host_name]
            },

            "output": [
                "hostid",
                "host",
                "name"
            ]
        }
    )


    if not hosts:

        return {
            "error":
                f"Host {host_name} not found"
        }


    host_id = hosts[0]["hostid"]


    # --------------------------------------------------------
    # Find CPU utilization item
    # --------------------------------------------------------

    items = zabbix_api(
        "item.get",
        {
            "hostids":
                host_id,

            "filter": {
                "key_": [
                    "system.cpu.util"
                ]
            },

            "output": [
                "itemid",
                "name",
                "key_",
                "lastvalue",
                "units"
            ]
        }
    )


    if not items:

        return {
            "error":
                "CPU utilization item not found "
                f"for {host_name}"
        }


    item = items[0]


    return {
        "host":
            host_name,

        "metric":
            item["name"],

        "value":
            float(item["lastvalue"]),

        "unit":
            item["units"],

        "item_id":
            item["itemid"]
    }


# ============================================================
# GET MEMORY USAGE
# ============================================================

def get_memory_usage(host_name):

    # --------------------------------------------------------
    # Find host
    # --------------------------------------------------------

    hosts = zabbix_api(
        "host.get",
        {
            "filter": {
                "host": [host_name]
            },

            "output": [
                "hostid",
                "host",
                "name"
            ]
        }
    )


    if not hosts:

        return {
            "error":
                f"Host {host_name} not found"
        }


    host_id = hosts[0]["hostid"]


    # --------------------------------------------------------
    # Find memory utilization item
    # --------------------------------------------------------

    items = zabbix_api(
        "item.get",
        {
            "hostids":
                host_id,

            "filter": {
                "key_": [
                    "vm.memory.util"
                ]
            },

            "output": [
                "itemid",
                "name",
                "key_",
                "lastvalue",
                "units"
            ]
        }
    )


    if not items:

        return {
            "error":
                "Memory utilization item not found "
                f"for {host_name}"
        }


    item = items[0]


    return {
        "host":
            host_name,

        "metric":
            item["name"],

        "value":
            float(item["lastvalue"]),

        "unit":
            item["units"],

        "item_id":
            item["itemid"]
    }
