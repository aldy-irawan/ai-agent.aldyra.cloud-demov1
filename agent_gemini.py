import os
import json

from dotenv import load_dotenv

from google import genai
from google.genai import types

from zabbix_tools import (
    get_all_hosts,
    get_active_problems,
    get_cpu_usage,
    get_memory_usage
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

API_KEY = os.environ["GEMINI_API_KEY"]


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=API_KEY
)


# ============================================================
# QUESTION INTENT
# ============================================================

def detect_question_intent(question):

    if not question:
        return "general_investigation"

    q = question.lower().strip()


    # --------------------------------------------------------
    # HOST LIST
    # --------------------------------------------------------

    host_keywords = [
        "server apa saja",
        "server mana saja",
        "host apa saja",
        "host mana saja",
        "what servers",
        "which servers",
        "list server",
        "list host",
        "berapa server",
        "ada server apa",
        "monitor server",
        "server yang dimonitor",
        "host yang dimonitor"
    ]

    if any(
        keyword in q
        for keyword in host_keywords
    ):
        return "host_list"


    # --------------------------------------------------------
    # MULTI HOST
    # --------------------------------------------------------

    multi_host_keywords = [
        "server mana yang bermasalah",
        "host mana yang bermasalah",
        "server paling bermasalah",
        "host paling bermasalah",
        "server paling urgent",
        "host paling urgent",
        "server paling critical",
        "host paling critical",
        "most problematic server",
        "most critical server",
        "most urgent server",
        "compare server",
        "compare hosts",
        "bandingkan server",
        "bandingkan host",
        "server mana yang paling",
        "host mana yang paling"
    ]

    if any(
        keyword in q
        for keyword in multi_host_keywords
    ):
        return "multi_host_analysis"


    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    health_keywords = [
        "sehat",
        "healthy",
        "health",
        "kondisi",
        "condition",
        "normal",
        "baik"
    ]

    if any(
        keyword in q
        for keyword in health_keywords
    ):
        return "health_check"


    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    cpu_keywords = [
        "cpu",
        "processor",
        "prosesor",
        "cpu usage",
        "cpu utilization",
        "cpu tinggi",
        "cpu paling tinggi",
        "highest cpu"
    ]

    if any(
        keyword in q
        for keyword in cpu_keywords
    ):
        return "cpu_analysis"


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    memory_keywords = [
        "memory",
        "memori",
        "ram",
        "memory usage",
        "memory utilization",
        "ram tinggi",
        "ram paling tinggi",
        "highest memory"
    ]

    if any(
        keyword in q
        for keyword in memory_keywords
    ):
        return "memory_analysis"


    # --------------------------------------------------------
    # PROBLEM
    # --------------------------------------------------------

    problem_keywords = [
        "problem",
        "warning",
        "alert",
        "issue",
        "error",
        "masalah",
        "kenapa",
        "why",
        "trouble",
        "troubleshoot"
    ]

    if any(
        keyword in q
        for keyword in problem_keywords
    ):
        return "problem_analysis"


    return "general_investigation"


# ============================================================
# OUTPUT MODE
# ============================================================

def detect_output_mode(question):

    if not question:
        return "detailed"

    q = question.lower().strip()

    detailed_keywords = [
        "analisis lengkap",
        "analisa lengkap",
        "analisis detail",
        "analisa detail",
        "secara detail",
        "selengkapnya",
        "investigasi lengkap",
        "investigasi detail",
        "full analysis",
        "detailed analysis",
        "complete analysis",
        "show all",
        "show details",
        "tampilkan semua",
        "tampilkan data",
        "jelaskan lengkap",
        "jelaskan detail",
        "laporan lengkap",
        "report lengkap"
    ]

    if any(
        keyword in q
        for keyword in detailed_keywords
    ):
        return "detailed"

    return "simple"


# ============================================================
# COLLECT ZABBIX DATA
# ============================================================

def collect_zabbix_data(verbose=True):

    collected_data = {

        "monitored_hosts": [],

        "active_problems": [],

        "cpu": [],

        "memory": []

    }


    # ========================================================
    # 1. GET ALL MONITORED HOSTS
    # ========================================================

    if verbose:

        print()
        print("------------------------------------------")
        print("MONITORED HOST COLLECTION")
        print("------------------------------------------")
        print()

        print(
            "Calling: get_all_hosts()"
        )


    try:

        monitored_hosts = get_all_hosts()

        if monitored_hosts is None:
            monitored_hosts = []


        collected_data[
            "monitored_hosts"
        ] = monitored_hosts


    except Exception as e:

        collected_data[
            "monitored_hosts"
        ] = []


        if verbose:

            print(
                "ERROR get_all_hosts:",
                str(e)
            )


    if verbose:

        print()
        print("MONITORED HOSTS:")

        print(
            json.dumps(
                collected_data[
                    "monitored_hosts"
                ],
                indent=2
            )
        )


    # ========================================================
    # 2. GET ACTIVE PROBLEMS
    # ========================================================

    if verbose:

        print()
        print("------------------------------------------")
        print("ACTIVE PROBLEM COLLECTION")
        print("------------------------------------------")
        print()

        print(
            "Calling: get_active_problems()"
        )


    try:

        active_problems = get_active_problems()

        if active_problems is None:
            active_problems = []


        collected_data[
            "active_problems"
        ] = active_problems


    except Exception as e:

        collected_data[
            "active_problems"
        ] = []


        if verbose:

            print(
                "ERROR get_active_problems:",
                str(e)
            )


    if verbose:

        print()
        print("ACTIVE PROBLEMS:")

        print(
            json.dumps(
                collected_data[
                    "active_problems"
                ],
                indent=2
            )
        )


    # ========================================================
    # 3. COLLECT RESOURCE DATA FOR ALL MONITORED HOSTS
    # ========================================================

    if verbose:

        print()
        print("------------------------------------------")
        print("ALL-HOST RESOURCE COLLECTION")
        print("------------------------------------------")
        print()


    for host in collected_data[
        "monitored_hosts"
    ]:

        if not isinstance(
            host,
            dict
        ):
            continue


        host_name = (
            host.get("name")
            or host.get("host")
        )


        if not host_name:
            continue


        if verbose:

            print(
                f"Processing host: {host_name}"
            )


        # ====================================================
        # CPU
        # ====================================================

        if verbose:

            print(
                f"Calling: get_cpu_usage("
                f"host_name='{host_name}')"
            )


        try:

            cpu_result = get_cpu_usage(
                host_name=host_name
            )


            if (
                cpu_result
                and isinstance(
                    cpu_result,
                    dict
                )
                and "error" not in cpu_result
            ):

                collected_data[
                    "cpu"
                ].append(
                    cpu_result
                )


            elif verbose:

                print(
                    f"CPU data unavailable "
                    f"for {host_name}"
                )


        except Exception as e:

            if verbose:

                print(
                    f"CPU error on "
                    f"{host_name}: {e}"
                )


        # ====================================================
        # MEMORY
        # ====================================================

        if verbose:

            print(
                f"Calling: get_memory_usage("
                f"host_name='{host_name}')"
            )


        try:

            memory_result = get_memory_usage(
                host_name=host_name
            )


            if (
                memory_result
                and isinstance(
                    memory_result,
                    dict
                )
                and "error" not in memory_result
            ):

                collected_data[
                    "memory"
                ].append(
                    memory_result
                )


            elif verbose:

                print(
                    f"Memory data unavailable "
                    f"for {host_name}"
                )


        except Exception as e:

            if verbose:

                print(
                    f"Memory error on "
                    f"{host_name}: {e}"
                )


    return collected_data


# ============================================================
# BUILD HOST SUMMARY
# ============================================================

def build_host_summary(collected_data):

    summary = {}


    # ========================================================
    # ALL MONITORED HOSTS
    # ========================================================

    for host in collected_data.get(
        "monitored_hosts",
        []
    ):

        if not isinstance(
            host,
            dict
        ):
            continue


        host_name = (
            host.get("name")
            or host.get("host")
        )


        if not host_name:
            continue


        summary[host_name] = {

            "host":
                host_name,

            "hostid":
                host.get("hostid"),

            "status":
                host.get("status"),

            "problems":
                [],

            "cpu":
                None,

            "memory":
                None

        }


    # ========================================================
    # ACTIVE PROBLEMS
    # ========================================================

    for problem in collected_data.get(
        "active_problems",
        []
    ):

        if not isinstance(
            problem,
            dict
        ):
            continue


        host_name = problem.get(
            "host"
        )


        if not host_name:
            continue


        if host_name not in summary:

            summary[host_name] = {

                "host":
                    host_name,

                "hostid":
                    None,

                "status":
                    None,

                "problems":
                    [],

                "cpu":
                    None,

                "memory":
                    None

            }


        summary[
            host_name
        ][
            "problems"
        ].append(
            problem
        )


    # ========================================================
    # CPU
    # ========================================================

    for cpu in collected_data.get(
        "cpu",
        []
    ):

        if not isinstance(
            cpu,
            dict
        ):
            continue


        host_name = cpu.get(
            "host"
        )


        if not host_name:
            continue


        if host_name not in summary:

            summary[host_name] = {

                "host":
                    host_name,

                "hostid":
                    None,

                "status":
                    None,

                "problems":
                    [],

                "cpu":
                    None,

                "memory":
                    None

            }


        summary[
            host_name
        ][
            "cpu"
        ] = cpu


    # ========================================================
    # MEMORY
    # ========================================================

    for memory in collected_data.get(
        "memory",
        []
    ):

        if not isinstance(
            memory,
            dict
        ):
            continue


        host_name = memory.get(
            "host"
        )


        if not host_name:
            continue


        if host_name not in summary:

            summary[host_name] = {

                "host":
                    host_name,

                "hostid":
                    None,

                "status":
                    None,

                "problems":
                    [],

                "cpu":
                    None,

                "memory":
                    None

            }


        summary[
            host_name
        ][
            "memory"
        ] = memory


    return list(
        summary.values()
    )


# ============================================================
# AI ACTION RECOMMENDATION PARSER
# ============================================================

def extract_action_recommendation(analysis):

    default = {
        "recommended_action": "none",
        "instance_name": None,
        "decision": "REVIEW",
        "reason": "No state-changing action was recommended.",
        "evidence": []
    }

    if not analysis:
        return default

    marker = "ACTION_RECOMMENDATION_JSON"
    position = analysis.rfind(marker)

    if position == -1:
        return default

    payload = analysis[position + len(marker):]

    decoder = json.JSONDecoder()

    start = payload.find("{")

    if start == -1:
        return default

    try:
        parsed, _ = decoder.raw_decode(
            payload[start:].lstrip()
        )
    except Exception:
        return default

    if not isinstance(parsed, dict):
        return default

    action = str(
        parsed.get("recommended_action", "none")
    ).strip().lower()

    if action not in {"stop", "none"}:
        action = "none"

    instance_name = parsed.get("instance_name")

    if instance_name is not None:
        instance_name = str(instance_name).strip() or None

    decision = str(
        parsed.get("decision", "REVIEW")
    ).strip().upper()

    if decision not in {"SAFE", "REVIEW", "NOT SAFE"}:
        decision = "REVIEW"

    reason = str(
        parsed.get(
            "reason",
            "No state-changing action was recommended."
        )
    ).strip()

    evidence = parsed.get("evidence", [])

    if isinstance(evidence, str):
        evidence = [evidence]

    if not isinstance(evidence, list):
        evidence = []

    evidence = [
        str(item).strip()
        for item in evidence
        if str(item).strip()
    ]

    return {
        "recommended_action": action,
        "instance_name": instance_name,
        "decision": decision,
        "reason": reason,
        "evidence": evidence
    }


# ============================================================
# GEMINI ANALYSIS
# ============================================================

def analyze_with_gemini(
    collected_data,
    question=None,
    intent="general_investigation",
    output_mode="simple",
    verbose=True
):

    host_summary = build_host_summary(
        collected_data
    )

    if verbose:

        print()
        print("------------------------------------------")
        print("GEMINI ANALYSIS")
        print("------------------------------------------")
        print()

        if question:

            print(
                "Question:",
                question
            )

            print(
                "Intent:",
                intent
            )

            print(
                "Output mode:",
                output_mode
            )

            print()

        print(
            "Sending Zabbix host dataset to Gemini..."
        )

    monitoring_json = json.dumps(
        {
            "monitored_hosts":
                collected_data.get(
                    "monitored_hosts",
                    []
                ),

            "active_problems":
                collected_data.get(
                    "active_problems",
                    []
                ),

            "hosts":
                host_summary
        },
        indent=2
    )

    # ========================================================
    # QUESTION MODE
    # ========================================================

    if question and output_mode == "simple":

        prompt = f"""
You are an AI Infrastructure Monitoring Assistant.

You are analyzing CURRENT infrastructure monitoring
data collected from Zabbix.

The Zabbix data below is the ONLY source of monitoring truth.

ZABBIX DATA:

{monitoring_json}


USER QUESTION:

{question}


DETECTED INTENT:

{intent}


OUTPUT MODE: SIMPLE

IMPORTANT RULES:

1. Answer the user's question directly and concisely.

2. Never invent monitoring data.

3. Use only the Zabbix data provided above.

4. Distinguish between monitored hosts and active problems.

5. A monitored host without an active problem is NOT
   automatically problematic.

6. Use CPU and memory only as supporting evidence when
   relevant to the question.

7. Zabbix problem severity has more weight than CPU or
   memory when determining urgency.

8. If the user asks whether a server is safe to stop,
   restart, or otherwise change, assess the available
   monitoring evidence first.

9. If there is an active relevant problem, do not describe
   the host as SAFE.

10. If the supplied data is insufficient to determine safety,
    use REVIEW or NOT SAFE rather than guessing.

11. Never invent host names or metric values.

12. Do not claim to have checked OS logs, filesystem,
    network configuration, security logs, or other systems
    unless that information exists in the supplied Zabbix data.

13. This is READ-ONLY analysis.

14. Do not perform remediation.

15. Do not output a long incident report in SIMPLE mode.

16. Do not output:
    - Incident
    - Current Conditions
    - Correlation Assessment
    - Likely Explanation
    - Event ID
    - Trigger ID
    - full CPU/memory tables
    unless the user explicitly asks for detailed analysis.

17. Keep the answer to approximately 3-5 short sentences.

18. When the question asks whether a host is safe for an
    action, begin with exactly one of:

    SAFE
    REVIEW
    NOT SAFE

19. After the decision, provide:
    - one short reason
    - one short recommendation

20. If the user asks a simple monitoring question that does
    not require SAFE/REVIEW/NOT SAFE, answer the question
    directly in a similarly concise format.

Respond clearly for an infrastructure engineer.
"""

    elif question:

        prompt = f"""
You are an AI Infrastructure Incident Analyst.

You are analyzing CURRENT infrastructure monitoring
data collected from Zabbix.

The Zabbix data provided below is the ONLY source
of monitoring truth.

Your job is to analyze the user's question while
correlating active problems with the current condition
of the affected infrastructure.

ZABBIX DATA:

{monitoring_json}


USER QUESTION:

{question}


DETECTED INTENT:

{intent}


IMPORTANT RULES:

1. Answer the user's question directly.

2. Never invent monitoring data.

3. Use only the Zabbix data provided above.

4. Distinguish clearly between:
   - MONITORED HOSTS
   - ACTIVE PROBLEMS
   - RESOURCE CONDITIONS

5. A monitored host without an active problem is NOT
   automatically problematic.

6. When analyzing an active problem, correlate it with:
   - the affected host
   - active problem severity
   - other active problems on the same host
   - CPU condition
   - memory condition
   - host monitoring status

7. Treat Zabbix problem severity as the primary
   indicator of urgency.

8. Treat CPU and memory as supporting evidence.

9. Look for CORRELATION:
   - Do current resource conditions support the problem?
   - Are there other active problems on the same host?
   - Is there evidence in the supplied Zabbix data that
     one condition may be related to another?
   - If the supplied data does not establish a relationship,
     explicitly say that the correlation cannot be confirmed.

10. Separate:
    - observed facts
    - correlation assessment
    - likely explanation

11. A "likely cause" must be described as a hypothesis
    unless the supplied Zabbix data directly supports it.

12. If data is missing, clearly state that it is unavailable.

13. Never invent host names.

14. Never invent metric values.

15. Do not claim to have checked:
    - OS logs
    - package history
    - filesystem
    - network
    - configuration
    - security logs
    - other systems

    unless that information exists in the supplied
    Zabbix data.

16. This is READ-ONLY analysis.

17. Do not perform remediation.

18. Do not recommend destructive or state-changing commands.

Respond clearly for an infrastructure engineer.

When the question is about an active incident, use
this structure where applicable:

## Incident Correlation

### 1. Incident
State the affected host, problem, severity and event
information available in Zabbix.

### 2. Current Conditions
State the currently observed CPU, memory, host status
and other relevant active problems.

### 3. Correlation Assessment
Explain whether the current conditions support the
incident and whether other observations correlate with it.

### 4. Likely Explanation
Provide the most reasonable explanation supported by the
available Zabbix data, clearly marking it as a hypothesis
when it is not confirmed.

### 5. Recommended Next Steps
Provide practical READ-ONLY verification steps for the
infrastructure engineer.
"""

    # ========================================================
    # GENERAL ANALYSIS
    # ========================================================

    else:

        prompt = f"""
You are an AI Infrastructure Incident Analyst.

You are analyzing CURRENT infrastructure monitoring
data collected from Zabbix.

The Zabbix data below is the ONLY source
of monitoring truth.

Your objective is to identify active incidents and
correlate them with the current infrastructure condition.

ZABBIX DATA:

{monitoring_json}


IMPORTANT RULES:

1. Never invent monitoring data.

2. Analyze all monitored hosts.

3. Distinguish between:
   - monitored hosts
   - hosts with active problems
   - current resource conditions

4. A host without an active problem must not be classified
   as problematic only because resource metrics exist.

5. For each monitored host identify, where data exists:
   - host
   - active problems
   - severity
   - CPU
   - memory
   - monitoring status

6. Identify which host requires the most attention.

7. Prioritize active Zabbix problem severity when
   determining urgency.

8. Use CPU and memory as supporting evidence.

9. Perform incident correlation:
   - correlate active problems with current CPU/memory
   - correlate multiple active problems on the same host
   - identify whether resource conditions support the
     observed problem
   - identify whether the available data suggests a
     common underlying condition

10. Do not claim correlation when the supplied data does
    not support it. State "correlation cannot be confirmed"
    when appropriate.

11. Separate:
    - observed facts
    - correlation assessment
    - likely explanation

12. Any likely cause must be treated as a hypothesis unless
    directly supported by supplied Zabbix data.

13. Do not invent missing values.

14. Do not claim to have checked logs or systems outside
    the supplied Zabbix data.

15. This is READ-ONLY analysis.

16. Do not perform remediation.

Produce:

## Infrastructure Incident Correlation Report

### 1. Monitoring Summary
State the number of monitored hosts and active problems.

### 2. Host-by-Host Assessment
Assess every monitored host for which data exists.

### 3. Active Incident Assessment
Identify the hosts with active problems and their severity.

### 4. Correlation Assessment
Correlate active problems with CPU, memory and other
active problems on the affected hosts.

### 5. Comparative Assessment
Identify the host requiring the most attention and explain why.

### 6. Likely Explanation
Provide reasonable hypotheses supported only by the supplied
Zabbix data and clearly label them as hypotheses.

### 7. Recommended Next Steps
Provide practical READ-ONLY verification steps for the
infrastructure engineer.
"""

# ========================================================
# MACHINE-READABLE ACTION RECOMMENDATION
# ========================================================

    prompt += f"""

IMPORTANT ACTION RECOMMENDATION RULES:

At the very end of your response, output a machine-readable
block named exactly:

ACTION_RECOMMENDATION_JSON
{{
  "recommended_action": "stop" or "none",
  "instance_name": "exact Zabbix host name" or null,
  "decision": "SAFE" or "REVIEW" or "NOT SAFE",
  "reason": "short explanation",
  "evidence": ["fact 1", "fact 2"]
}}

ACTION DECISION LOGIC:

1. This recommendation is ADVISORY ONLY.
   NEVER execute or simulate the action.

2. Use ONLY the supplied Zabbix monitoring data.

3. "instance_name" MUST exactly match a monitored Zabbix host name.

4. The only currently supported state-changing action is:
   - stop

5. Recommend "stop" ONLY when ALL of the following are true:
   - the affected host is clearly identified;
   - the host has an active Zabbix problem;
   - the available monitoring evidence indicates that intervention
     on the host is reasonably justified;
   - stopping the host is a reasonable candidate action based on
     the observed condition;
   - there is no supplied evidence indicating that stopping the
     host would be unsafe.

6. Do NOT recommend "stop" merely because:
   - a host has a Warning severity;
   - a host has high CPU;
   - a host has high memory;
   - a metric is temporarily abnormal;
   - a single alert exists without sufficient context.

7. If the active problem can reasonably be investigated or
   remediated without stopping the host, prefer:
   "recommended_action": "none"

8. If the monitoring evidence is insufficient to justify a
   state-changing action, use:

   "recommended_action": "none"
   "decision": "REVIEW"

9. If the supplied monitoring evidence indicates that stopping
   the host could be unsafe, use:

   "recommended_action": "none"
   "decision": "NOT SAFE"

10. Use "SAFE" only when the supplied monitoring evidence provides
    strong evidence that the action is appropriate and no relevant
    risk is visible in the supplied dataset.

11. A state-changing recommendation NEVER means automatic execution.
    Human approval is always required.

12. Never invent:
    - AWS instance IDs
    - AWS regions
    - IP addresses
    - CPU values
    - memory values
    - host names
    - infrastructure conditions

13. Evidence must contain actual facts observed in the supplied
    Zabbix dataset.

14. If there is no justified state-changing action, return:

{{
  "recommended_action": "none",
  "instance_name": null,
  "decision": "REVIEW",
  "reason": "No state-changing action is sufficiently justified by the available monitoring evidence.",
  "evidence": []
}}

15. If a stop recommendation is justified, return:

{{
  "recommended_action": "stop",
  "instance_name": "EXACT_HOST_NAME",
  "decision": "REVIEW",
  "reason": "short monitoring-based reason",
  "evidence": [
    "actual Zabbix evidence",
    "actual Zabbix evidence"
  ]
}}

16. Do not put any text after the JSON block.
    """
    # ========================================================
    # ONE GEMINI REQUEST
    # ========================================================

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text=prompt
                    )
                ]
            )
        ]
    )

    if verbose:

        print()
        print(
            "Gemini request count: 1"
        )

    analysis = response.text

    if not analysis:

        analysis = (
            "Gemini returned an empty analysis."
        )

    action_recommendation = extract_action_recommendation(
        analysis
    )

    marker_position = analysis.rfind(
        "ACTION_RECOMMENDATION_JSON"
    )

    if marker_position != -1:
        analysis = analysis[:marker_position].rstrip()

    return analysis, action_recommendation

# ============================================================
# RUN AGENT
# ============================================================

def run_agent(
    question=None,
    output_mode=None,
    verbose=True
):

    # --------------------------------------------------------
    # STEP 1
    # Collect Zabbix data
    # --------------------------------------------------------

    collected_data = collect_zabbix_data(
        verbose=verbose
    )


    # --------------------------------------------------------
    # STEP 2
    # Detect intent
    # --------------------------------------------------------

    intent = detect_question_intent(
        question
    )

    if output_mode is None:
        output_mode = detect_output_mode(
        question
    )


    if verbose and question:

        print()
        print("------------------------------------------")
        print("QUESTION INTENT")
        print("------------------------------------------")
        print()

        print(
            "Question:",
            question
        )

        print(
            "Intent:",
            intent
        )

        print(
            "Output mode:",
            output_mode
        )


    # --------------------------------------------------------
    # STEP 3
    # Build host summary
    # --------------------------------------------------------

    host_summary = build_host_summary(
        collected_data
    )


    # --------------------------------------------------------
    # STEP 4
    # Gemini analysis
    # --------------------------------------------------------

    analysis, action_recommendation = analyze_with_gemini(

        collected_data,

        question=question,

        intent=intent,

        output_mode=output_mode,

        verbose=verbose
    )


    # --------------------------------------------------------
    # STEP 5
    # Structured result
    # --------------------------------------------------------

    result = {

        "monitored_hosts":
            collected_data.get(
                "monitored_hosts",
                []
            ),

        "active_problems":
            collected_data.get(
                "active_problems",
                []
            ),

        "cpu":
            collected_data.get(
                "cpu",
                []
            ),

        "memory":
            collected_data.get(
                "memory",
                []
            ),

        "hosts":
            host_summary,

        "host_count":
            len(host_summary),

        "intent":
            intent,

        "output_mode":
            output_mode,

        "analysis":
            analysis,

        "action_recommendation":
            action_recommendation

    }


    return result


# ============================================================
# DIRECT EXECUTION
# ============================================================

if __name__ == "__main__":

    print()
    print("==========================================")
    print("       ZABBIX AI INFRASTRUCTURE AGENT")
    print("==========================================")
    print()


    try:

        result = run_agent(
            verbose=True
        )


        print()
        print("------------------------------------------")
        print("MULTI-HOST STRUCTURED RESULT")
        print("------------------------------------------")
        print()


        print(
            json.dumps(
                result,
                indent=2
            )
        )


        print()
        print("==========================================")
        print("              AI ANALYSIS")
        print("==========================================")
        print()


        print(
            result["analysis"]
        )


        print()
        print("==========================================")
        print("                COMPLETE")
        print("==========================================")
        print()


    except Exception as e:

        print()
        print("==========================================")
        print("                 ERROR")
        print("==========================================")
        print()

        print(
            str(e)
        )
