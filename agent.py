from zabbix_tools import (
    get_active_problems,
    get_cpu_usage,
    get_memory_usage
)

import json


def investigate():

    print("=== ZABBIX AI AGENT ===")
    print()

    # 1. Get active problems
    problems = get_active_problems()

    print(f"Active problems: {len(problems)}")
    print()

    if not problems:
        print("No active problems.")
        return

    # 2. Investigate each problem
    for problem in problems:

        host = problem["host"]

        print("--------------------------------")
        print(f"Host     : {host}")
        print(f"Problem  : {problem['problem']}")
        print(f"Severity : {problem['severity']}")
        print("--------------------------------")

        # 3. Check CPU
        cpu = get_cpu_usage(host)

        # 4. Check Memory
        memory = get_memory_usage(host)

        print()
        print("CPU:")
        print(json.dumps(cpu, indent=2))

        print()
        print("Memory:")
        print(json.dumps(memory, indent=2))

        print()


if __name__ == "__main__":
    investigate()
