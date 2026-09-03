
import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from agent_gemini import run_agent


app = FastAPI(
    title="Zabbix AI Infrastructure Agent",
    description="AI monitoring analysis using Zabbix and Gemini",
    version="1.0",
)
app.include_router(action_router)

# ============================================================
# INVESTIGATION HISTORY STORAGE
# ============================================================

from investigation_store import (
    find_investigation_by_event,
    get_investigations,
    init_db,
    save_investigation,
    update_investigation,
)

init_db()


# ============================================================
# REQUEST MODELS
# ============================================================

class AskRequest(BaseModel):
    question: str
    mode: str = "simple"


class ZabbixWebhookRequest(BaseModel):
    event_id: str | None = None
    host: str | None = None
    problem: str | None = None
    severity: str | None = None
    trigger_id: str | None = None


# ============================================================
# WEB UI
# ============================================================

HTML_PAGE = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zabbix AI Infrastructure Agent</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,Helvetica,sans-serif;background:#f4f6f8;color:#1f2937}
.header{background:#111827;color:#fff;padding:22px 40px}
.header h1{margin:0;font-size:24px}
.header p{margin:6px 0 0;color:#9ca3af;font-size:14px}
.container{max-width:1200px;margin:35px auto;padding:0 20px}
.card{background:#fff;border-radius:12px;padding:25px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,.08)}
.status,.ai-badge{display:inline-block;padding:6px 12px;border-radius:20px;font-size:13px;font-weight:bold}
.status{background:#dcfce7;color:#166534}
.ai-badge{background:#ede9fe;color:#6d28d9}
.result-header{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:20px}
.button-container{text-align:center;padding:15px}
button{background:#2563eb;color:#fff;border:none;border-radius:8px;padding:14px 30px;font-size:16px;font-weight:bold;cursor:pointer}
button:hover{background:#1d4ed8}
button:disabled{background:#9ca3af;cursor:wait}
.loading{display:none;text-align:center;padding:20px;color:#6b7280}
.summary-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-top:20px}
.summary-box{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:20px}
.summary-label{font-size:13px;color:#64748b;text-transform:uppercase;margin-bottom:8px}
.summary-value{font-size:28px;font-weight:bold;color:#111827}
.resource-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:15px;margin-top:20px}
.resource-box{background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:20px}
.resource-title{color:#64748b;font-size:13px;text-transform:uppercase;margin-bottom:8px}
.resource-value{font-size:30px;font-weight:bold;color:#111827}
.table-wrapper{overflow-x:auto;margin-top:20px}
.data-table{width:100%;border-collapse:collapse;min-width:900px}
.data-table th{text-align:left;background:#f8fafc;color:#64748b;font-size:12px;text-transform:uppercase;padding:14px;border-bottom:1px solid #e5e7eb}
.data-table td{padding:14px;border-bottom:1px solid #e5e7eb;font-size:13px;vertical-align:top}
.data-table tr:last-child td{border-bottom:none}
.host-name{font-weight:bold;color:#111827}
.host-status-ok,.host-status-warning,.host-status-high{display:inline-block;padding:5px 10px;border-radius:15px;font-size:12px;font-weight:bold}
.host-status-ok{background:#dcfce7;color:#166534}
.host-status-warning{background:#fef3c7;color:#92400e}
.host-status-high{background:#fee2e2;color:#991b1b}
.problem{background:#fffbeb;border-left:5px solid #f59e0b;border-radius:8px;padding:18px;margin-top:12px}
.problem-title{font-weight:bold;font-size:16px;margin-bottom:10px}
.problem-detail{font-size:14px;margin:5px 0}
.result{display:none}
.analysis{white-space:pre-wrap;word-wrap:break-word;line-height:1.7;font-size:14px}
.history-analysis{max-width:550px;max-height:180px;overflow:auto;white-space:pre-wrap}
.history-status{display:inline-block;padding:5px 10px;border-radius:15px;font-size:12px;font-weight:bold;text-transform:uppercase}
.history-status-success{background:#dcfce7;color:#166534}
.history-status-processing{background:#dbeafe;color:#1d4ed8}
.history-status-failed{background:#fee2e2;color:#991b1b}
.history-status-unknown{background:#e5e7eb;color:#374151}
.history-duration{white-space:nowrap;font-weight:bold}

.history-row{cursor:pointer;transition:background .15s ease}
.history-row:hover,.history-row.expanded{background:#f8fafc}
.history-chevron{display:inline-block;margin-right:6px;font-size:12px;transition:transform .15s ease}
.history-row.expanded .history-chevron{transform:rotate(90deg)}
.history-detail-row{display:none}
.history-detail-row.open{display:table-row}
.history-detail-cell{background:#fbfdff;border-bottom:1px solid #e5e7eb;padding:18px 20px}
.history-detail-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:14px}
.history-detail-box{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:12px}
.history-detail-label{font-size:11px;color:#64748b;text-transform:uppercase;margin-bottom:5px}
.history-detail-value{font-size:13px;color:#111827;word-break:break-word}
.history-detail-analysis{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:15px;max-height:320px;overflow:auto;white-space:pre-wrap;line-height:1.65;font-size:13px}

.ask-input{display:flex;gap:10px;margin-top:15px}
.ask-input input{flex:1;padding:14px;border:1px solid #d1d5db;border-radius:8px;font-size:15px;outline:none}
.ask-input input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.1)}
.error{display:none;background:#fee2e2;color:#991b1b;padding:15px;border-radius:8px;margin-top:15px}
.action-panel{border:1px solid #e5e7eb;border-radius:10px;padding:20px;background:#fbfdff;margin-top:15px}
.action-grid{display:grid;grid-template-columns:160px 1fr;gap:12px 15px;align-items:center;margin-top:15px}
.action-label{font-size:12px;color:#64748b;text-transform:uppercase;font-weight:bold}
.action-value{font-size:14px;color:#111827;font-weight:600}
.action-warning{background:#fffbeb;border:1px solid #f59e0b;color:#92400e;border-radius:8px;padding:14px;margin:15px 0;line-height:1.5}
.action-buttons{display:flex;gap:10px;flex-wrap:wrap;margin-top:18px}
.action-confirm{background:#b91c1c}
.action-confirm:hover{background:#991b1b}
.action-cancel{background:#6b7280}
.action-cancel:hover{background:#4b5563}
.action-propose{background:#7c3aed}
.action-propose:hover{background:#6d28d9}
.action-result{margin-top:15px;padding:14px;border-radius:8px;white-space:pre-wrap;line-height:1.5}
.action-result.success{background:#dcfce7;color:#166534;border:1px solid #86efac}
.action-result.error{background:#fee2e2;color:#991b1b;border:1px solid #fca5a5}
.action-muted{color:#64748b;font-size:13px}

.footer{text-align:center;color:#9ca3af;font-size:12px;padding:20px}
@media(max-width:850px){.summary-grid{grid-template-columns:repeat(2,1fr)}.resource-grid{grid-template-columns:1fr}.history-detail-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.summary-grid{grid-template-columns:1fr}.ask-input{flex-direction:column}.history-detail-grid{grid-template-columns:1fr}}
</style>
</head>

<body>

<div class="header">
<h1>Zabbix AI Infrastructure Agent</h1>
<p>AI-powered infrastructure investigation using Zabbix + Gemini</p>
</div>

<div class="container">

<div class="card">
<div class="result-header">
<h2>Infrastructure Monitoring</h2>
<span class="status">READY</span>
</div>
<p>AI Agent Status: <strong>Operational</strong></p>
<p>Monitoring Source: <strong>Zabbix</strong></p>
<p>AI Engine: <strong>Google Gemini</strong></p>
</div>

<div class="card">
<div class="button-container">
<button id="analyzeButton" onclick="runAnalysis()">🔍 RUN AI ANALYSIS</button>
</div>
<div id="loading" class="loading">🤖 AI Agent is investigating the infrastructure...</div>
<div id="error" class="error"></div>
</div>

<div id="summaryCard" class="card result">
<h2>Infrastructure Summary</h2>
<div class="summary-grid">
<div class="summary-box"><div class="summary-label">Monitored Hosts</div><div id="hostCount" class="summary-value">0</div></div>
<div class="summary-box"><div class="summary-label">Active Problems</div><div id="problemCount" class="summary-value">0</div></div>
<div class="summary-box"><div class="summary-label">Highest CPU</div><div id="highestCPU" class="summary-value">-</div></div>
<div class="summary-box"><div class="summary-label">Highest Memory</div><div id="highestMemory" class="summary-value">-</div></div>
</div>
</div>

<div id="hostsCard" class="card result">
<div class="result-header"><h2>Monitored Hosts</h2><span class="ai-badge">ZABBIX</span></div>
<div class="table-wrapper">
<table class="data-table">
<thead><tr><th>Host</th><th>Status</th><th>Active Problems</th><th>CPU</th><th>Memory</th></tr></thead>
<tbody id="hostTableBody"></tbody>
</table>
</div>
</div>

<div id="problemsCard" class="card result">
<div class="result-header"><h2>Active Problems</h2><span class="ai-badge">ZABBIX</span></div>
<div id="problemsContainer"></div>
</div>

<div id="resourceCard" class="card result">
<h2>Resource Utilization</h2>
<div class="resource-grid">
<div class="resource-box"><div class="resource-title">Highest CPU</div><div id="cpuValue" class="resource-value">-</div></div>
<div class="resource-box"><div class="resource-title">Highest Memory</div><div id="memoryValue" class="resource-value">-</div></div>
</div>
</div>

<div id="analysisCard" class="card result">
<div class="result-header"><h2>AI Analysis</h2><span class="ai-badge">GEMINI AI</span></div>
<div id="analysisText" class="analysis"></div>
</div>

<div class="card">
<div class="result-header"><h2>Ask AI Infrastructure Assistant</h2><span class="ai-badge">GEMINI AI</span></div>
<p>Ask a question about the current infrastructure condition.</p>
<div class="ask-input">
<input type="text" id="questionInput" placeholder="Example: Which server has the highest CPU?">
<button id="askButton" onclick="askAI()">🤖 ASK AI</button>
</div>
<div id="askLoading" class="loading">🤖 AI is analyzing your question...</div>
<div id="askError" class="error"></div>
</div>

<div id="askResult" class="card result">
<div class="result-header"><h2>AI Answer</h2><span class="ai-badge">GEMINI AI</span></div>
<div id="answerText" class="analysis"></div>
</div>

<div id="actionCard" class="card" style="display:none;">
<div class="result-header"><h2>Action Manager</h2><span class="ai-badge">CONTROLLED ACTION</span></div>
<p class="action-muted">Actions are executed only after a successful proposal check and explicit human confirmation.</p>

<div class="action-panel">

<div class="action-grid">
<div class="action-label">Action</div>
<div class="action-value">STOP EC2</div>

<div class="action-label">Instance Name</div>
<div>
<input
    type="text"
    id="actionInstanceName"
    placeholder="Example: AI-DEMO-EC2"
    style="width:100%;padding:12px;border:1px solid #d1d5db;border-radius:8px;font-size:14px;">
</div>
</div>

<div class="action-buttons">
<button
    id="proposeActionButton"
    class="action-propose"
    onclick="proposeEC2Stop()">
    ⚡ PROPOSE STOP
</button>
</div>

<div id="actionLoading" class="loading">🔎 Checking EC2 and creating action proposal...</div>
<div id="actionError" class="error"></div>

<div id="proposalPanel" style="display:none;">
<div class="action-warning">
<strong>⚠ HUMAN CONFIRMATION REQUIRED</strong><br>
The proposal has passed the initial safety check. The EC2 instance will NOT be stopped until you explicitly confirm the action.
</div>

<div class="action-grid">
<div class="action-label">Proposal ID</div>
<div id="proposalId" class="action-value">-</div>

<div class="action-label">Instance ID</div>
<div id="proposalInstanceId" class="action-value">-</div>

<div class="action-label">Region</div>
<div id="proposalRegion" class="action-value">-</div>

<div class="action-label">Current State</div>
<div id="proposalState" class="action-value">-</div>

<div class="action-label">Decision</div>
<div id="proposalDecision" class="action-value">-</div>
</div>

<div class="action-buttons">
<button
    id="confirmActionButton"
    class="action-confirm"
    onclick="confirmEC2Stop()">
    🛑 CONFIRM &amp; EXECUTE STOP
</button>

<button
    id="cancelActionButton"
    class="action-cancel"
    onclick="cancelActionProposal()">
    CANCEL
</button>
</div>

<div id="executionLoading" class="loading">⚙️ Executing approved EC2 action...</div>
<div id="executionResult"></div>
</div>

</div>
</div>

<div class="card">
<div class="result-header"><h2>Investigation History</h2>
<div class="card">
<div class="result-header"><h2>Investigation History</h2><span class="ai-badge">AI HISTORY</span></div>
<div class="table-wrapper">
<table class="data-table">
<thead>
<tr><th></th><th>ID</th><th>Time</th><th>Event</th><th>Host</th><th>Severity</th><th>Problem</th><th>Status</th><th>Duration</th></tr>
</thead>
<tbody id="historyTableBody">
<tr><td colspan="9">Loading...</td></tr>
</tbody>
</table>
</div>
</div>

</div>

<div class="footer">
Zabbix AI Infrastructure Agent · Read-only monitoring analysis
</div>

<script>
function escapeHtml(value){
    if(value===null||value===undefined){return "";}
    return String(value)
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;")
        .replace(/"/g,"&quot;")
        .replace(/'/g,"&#039;");
}

function cleanAIText(value){

    if(
        value === null ||
        value === undefined
    ){
        return "";
    }

    return String(value)
        .replace(/[*#]/g, "");
}

async function runAnalysis(){
    const button=document.getElementById("analyzeButton");
    const loading=document.getElementById("loading");
    const error=document.getElementById("error");

    button.disabled=true;
    button.textContent="⏳ ANALYZING...";
    loading.style.display="block";
    error.style.display="none";

    try{
        const response=await fetch("/analyze");
        if(!response.ok){throw new Error("HTTP error: "+response.status);}

        const data=await response.json();

        if(data.status!=="success"){
            throw new Error(data.error||"AI analysis failed");
        }

        const hosts=data.monitored_hosts||[];
        const problems=data.active_problems||[];
        const cpu=data.cpu||[];
        const memory=data.memory||[];

        document.getElementById("hostCount").textContent=hosts.length;
        document.getElementById("problemCount").textContent=problems.length;

        if(cpu.length){
            const highest=[...cpu].sort(
                (a,b)=>Number(b.value)-Number(a.value)
            )[0];

            const value=Number(highest.value).toFixed(2);

            document.getElementById("highestCPU").textContent=value+"%";
            document.getElementById("cpuValue").textContent=
                value+"% — "+highest.host;

        }else{
            document.getElementById("highestCPU").textContent="N/A";
            document.getElementById("cpuValue").textContent="N/A";
        }

        if(memory.length){
            const highest=[...memory].sort(
                (a,b)=>Number(b.value)-Number(a.value)
            )[0];

            const value=Number(highest.value).toFixed(2);

            document.getElementById("highestMemory").textContent=value+"%";
            document.getElementById("memoryValue").textContent=
                value+"% — "+highest.host;

        }else{
            document.getElementById("highestMemory").textContent="N/A";
            document.getElementById("memoryValue").textContent="N/A";
        }

        const hostMap={};

        hosts.forEach(host=>{
            const name=host.name||host.host;

            if(name){
                hostMap[name]={
                    name:name,
                    problems:[],
                    cpu:null,
                    memory:null
                };
            }
        });

        problems.forEach(problem=>{
            const name=problem.host;

            if(!name){return;}

            if(!hostMap[name]){
                hostMap[name]={
                    name:name,
                    problems:[],
                    cpu:null,
                    memory:null
                };
            }

            hostMap[name].problems.push(problem);
        });

        cpu.forEach(item=>{
            const name=item.host;

            if(!name){return;}

            if(!hostMap[name]){
                hostMap[name]={
                    name:name,
                    problems:[],
                    cpu:null,
                    memory:null
                };
            }

            hostMap[name].cpu=item;
        });

        memory.forEach(item=>{
            const name=item.host;

            if(!name){return;}

            if(!hostMap[name]){
                hostMap[name]={
                    name:name,
                    problems:[],
                    cpu:null,
                    memory:null
                };
            }

            hostMap[name].memory=item;
        });

        const tableBody=document.getElementById("hostTableBody");
        tableBody.innerHTML="";

        Object.values(hostMap).forEach(host=>{
            const problemCount=host.problems.length;

            let statusClass="host-status-ok";
            let statusText="Normal";

            if(problemCount>0){
                let highestPriority=0;

                host.problems.forEach(problem=>{
                    const severity=String(
                        problem.severity||""
                    ).toLowerCase();

                    const priorityMap={
                        warning:2,
                        average:3,
                        high:4,
                        disaster:5
                    };

                    highestPriority=Math.max(
                        highestPriority,
                        priorityMap[severity]||0
                    );
                });

                statusClass=
                    highestPriority>=4
                    ?"host-status-high"
                    :"host-status-warning";

                statusText=
                    problemCount+
                    " Problem"+
                    (problemCount>1?"s":"");
            }

            const cpuText=
                host.cpu
                ?Number(host.cpu.value).toFixed(2)+"%"
                :"N/A";

            const memoryText=
                host.memory
                ?Number(host.memory.value).toFixed(2)+"%"
                :"N/A";

            tableBody.innerHTML+=
                "<tr>"+
                "<td><span class='host-name'>"+
                escapeHtml(host.name)+
                "</span></td>"+
                "<td><span class='"+statusClass+"'>"+
                escapeHtml(statusText)+
                "</span></td>"+
                "<td>"+problemCount+"</td>"+
                "<td>"+cpuText+"</td>"+
                "<td>"+memoryText+"</td>"+
                "</tr>";
        });

        const problemsContainer=
            document.getElementById("problemsContainer");

        problemsContainer.innerHTML="";

        if(!problems.length){

            problemsContainer.innerHTML=
                "<div class='problem' "+
                "style='border-left-color:#22c55e;background:#f0fdf4'>"+
                "<div class='problem-title'>"+
                "🟢 No Active Problems"+
                "</div>"+
                "<div class='problem-detail'>"+
                "Zabbix currently reports no active infrastructure problems."+
                "</div>"+
                "</div>";

        }else{

            problems.forEach(problem=>{

                problemsContainer.innerHTML+=
                    "<div class='problem'>"+
                    "<div class='problem-title'>⚠️ "+
                    escapeHtml(problem.problem)+
                    "</div>"+
                    "<div class='problem-detail'><strong>Host:</strong> "+
                    escapeHtml(problem.host)+
                    "</div>"+
                    "<div class='problem-detail'><strong>Severity:</strong> "+
                    escapeHtml(problem.severity)+
                    "</div>"+
                    "<div class='problem-detail'><strong>Trigger ID:</strong> "+
                    escapeHtml(problem.trigger_id)+
                    "</div>"+
                    "<div class='problem-detail'><strong>Event ID:</strong> "+
                    escapeHtml(problem.event_id)+
                    "</div>"+
                    "</div>";
            });
        }

        document.getElementById("analysisText").textContent=
            cleanAIText(data.analysis||"");

        [
            "summaryCard",
            "hostsCard",
            "problemsCard",
            "resourceCard",
            "analysisCard"
        ].forEach(
            id=>{
                document.getElementById(id).style.display="block";
            }
        );

    }catch(errorObject){

        error.textContent=
            "Error: "+
            errorObject.message;

        error.style.display="block";

    }finally{

        button.disabled=false;
        button.textContent="🔍 RUN AI ANALYSIS";
        loading.style.display="none";
    }
}


async function askAI(){

    const input=document.getElementById("questionInput");
    const button=document.getElementById("askButton");
    const loading=document.getElementById("askLoading");
    const result=document.getElementById("askResult");
    const answerText=document.getElementById("answerText");
    const error=document.getElementById("askError");

    const question=input.value.trim();

    if(!question){

        error.textContent=
            "Please enter a question.";

        error.style.display=
            "block";

        return;
    }

    result.style.display="none";
    error.style.display="none";

    button.disabled=true;
    button.textContent="⏳ ASKING...";
    loading.style.display="block";

    try{

        const response=
            await fetch(
                "/ask",
                {
                    method:"POST",
                    headers:{
                        "Content-Type":
                            "application/json"
                    },
                    body:
                        JSON.stringify({
                            question:question
                        })
                }
            );

        if(!response.ok){
            throw new Error(
                "HTTP error: "+
                response.status
            );
        }

        const data=
            await response.json();

        if(data.status!=="success"){
            throw new Error(
                data.error||
                "AI request failed"
            );
        }

        if(
            data.answer &&
            typeof data.answer==="object"
        ){

            answerText.textContent=
                cleanAIText(
                    data.answer.analysis||
                    JSON.stringify(
                        data.answer,
                        null,
                        2
                    )
                );

        }else{

            answerText.textContent=
                data.answer;
        }


        result.style.display="block";

        const actionQuestion =
            question.toLowerCase();

        const actionKeywords = [
            "matikan",
            "dimatikan",
            "stop",
            "shutdown",
            "hentikan",
            "restart",
            "reboot"
        ];

        if(
            actionKeywords.some(
                keyword => actionQuestion.includes(keyword)
            )
        ){
            showActionCard();

            const instanceInput =
                document.getElementById(
                    "actionInstanceName"
                );

            if(
                instanceInput &&
                !instanceInput.value
            ){
                const match =
                    question.match(
                        /(?:server|host|instance)\s+([A-Za-z0-9._-]+)/i
                    );

                if(match && match[1]){
                    instanceInput.value=match[1];
                }
            }
        }

    }catch(errorObject){

        error.textContent=
            "Error: "+
            errorObject.message;

        error.style.display="block";

    }finally{

        button.disabled=false;
        button.textContent="🤖 ASK AI";
        loading.style.display="none";
    }
}


let currentActionProposalId = null;

function showActionCard(){
    const card=document.getElementById("actionCard");
    if(card){
        card.style.display="block";
    }
}

function clearActionError(){
    const error=document.getElementById("actionError");
    if(error){
        error.textContent="";
        error.style.display="none";
    }
}

function cancelActionProposal(){
    currentActionProposalId=null;

    const panel=document.getElementById("proposalPanel");
    const result=document.getElementById("executionResult");

    if(panel){
        panel.style.display="none";
    }

    if(result){
        result.innerHTML="";
    }

    clearActionError();
}

async function proposeEC2Stop(){

    const input=document.getElementById("actionInstanceName");
    const button=document.getElementById("proposeActionButton");
    const loading=document.getElementById("actionLoading");
    const error=document.getElementById("actionError");
    const panel=document.getElementById("proposalPanel");

    const instanceName=input.value.trim();

    clearActionError();

    if(!instanceName){
        error.textContent="Please enter an EC2 instance Name tag.";
        error.style.display="block";
        return;
    }

    currentActionProposalId=null;

    if(panel){
        panel.style.display="none";
    }

    button.disabled=true;
    button.textContent="⏳ CHECKING...";
    loading.style.display="block";

    try{

        const response=await fetch(
            "/action/propose",
            {
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    action:"stop",
                    instance_name:instanceName
                })
            }
        );

        const data=await response.json();

        if(!response.ok){
            throw new Error(
                data.detail ||
                data.message ||
                "Action proposal failed"
            );
        }

        if(data.status!=="success"){
            throw new Error(
                data.message ||
                "Action proposal was rejected"
            );
        }

        currentActionProposalId=data.proposal_id;

        document.getElementById("proposalId").textContent=data.proposal_id || "-";
        document.getElementById("proposalInstanceId").textContent=data.instance_id || "-";
        document.getElementById("proposalRegion").textContent=data.region || "-";
        document.getElementById("proposalState").textContent=data.current_state || "-";
        document.getElementById("proposalDecision").textContent=data.decision || "-";

        panel.style.display="block";

        document.getElementById("executionResult").innerHTML="";

    }catch(errorObject){

        error.textContent="Error: "+errorObject.message;
        error.style.display="block";

    }finally{

        button.disabled=false;
        button.textContent="⚡ PROPOSE STOP";
        loading.style.display="none";
    }
}

async function confirmEC2Stop(){

    const button=document.getElementById("confirmActionButton");
    const cancelButton=document.getElementById("cancelActionButton");
    const loading=document.getElementById("executionLoading");
    const result=document.getElementById("executionResult");
    const error=document.getElementById("actionError");

    clearActionError();

    if(!currentActionProposalId){
        error.textContent="No pending action proposal.";
        error.style.display="block";
        return;
    }

    const confirmed=window.confirm(
        "CONFIRM STOP\n\n" +
        "This will execute the approved EC2 STOP action.\n\n" +
        "Proposal: " + currentActionProposalId + "\n\n" +
        "Continue?"
    );

    if(!confirmed){
        return;
    }

    button.disabled=true;
    cancelButton.disabled=true;
    loading.style.display="block";
    result.innerHTML="";

    try{

        const response=await fetch(
            "/action/confirm",
            {
                method:"POST",
                headers:{
                    "Content-Type":"application/json"
                },
                body:JSON.stringify({
                    proposal_id:currentActionProposalId
                })
            }
        );

        const data=await response.json();

        if(!response.ok){
            throw new Error(
                data.detail ||
                data.message ||
                "Action execution failed"
            );
        }

        if(data.status!=="success"){
            throw new Error(
                data.message ||
                data.error ||
                "Action execution failed"
            );
        }

        result.className="action-result success";
        result.textContent=
            "✅ ACTION SUCCESS\n\n" +
            "Instance: " + (data.instance_name || "-") + "\n" +
            "Instance ID: " + (data.instance_id || "-") + "\n" +
            "Region: " + (data.region || "-") + "\n" +
            "Previous State: " + (data.previous_state || "-") + "\n" +
            "Execution Status: " + (data.execution_status || "-") + "\n\n" +
            (data.message || "");

        currentActionProposalId=null;

        document.getElementById("proposalPanel").style.display="none";

    }catch(errorObject){

        result.className="action-result error";
        result.textContent=
            "❌ ACTION FAILED\n\n" +
            errorObject.message;

    }finally{

        button.disabled=false;
        cancelButton.disabled=false;
        loading.style.display="none";
    }
}


function toggleHistoryRow(rowId){

    const row =
        document.getElementById(
            "history-row-" + rowId
        );

    const detail =
        document.getElementById(
            "history-detail-" + rowId
        );

    if (!row || !detail) {
        return;
    }

    const isOpen =
        detail.classList.contains("open");

    document
        .querySelectorAll(
            ".history-detail-row.open"
        )
        .forEach(
            function(item){
                item.classList.remove("open");
            }
        );

    document
        .querySelectorAll(
            ".history-row.expanded"
        )
        .forEach(
            function(item){
                item.classList.remove("expanded");
            }
        );

    if (!isOpen) {

        detail.classList.add("open");
        row.classList.add("expanded");

    }
}


async function loadHistory(){

    const body =
        document.getElementById(
            "historyTableBody"
        );

    try {

        const response =
            await fetch(
                "/investigations?limit=50"
            );

        if (!response.ok) {
            throw new Error(
                "HTTP error: " +
                response.status
            );
        }

        const data =
            await response.json();

        if (
            !data.items ||
            data.items.length === 0
        ) {

            body.innerHTML =
                "<tr><td colspan='9'>" +
                "No investigation history yet." +
                "</td></tr>";

            return;
        }

        body.innerHTML = "";

        data.items.forEach(
            function(item, index){

                const rowId =
                    String(
                        item.id ||
                        ("history-" + index)
                    ).replace(
                        /[^a-zA-Z0-9_-]/g,
                        "_"
                    );

                const status =
                    String(
                        item.status || "unknown"
                    ).toLowerCase();

                let statusClass =
                    "history-status-unknown";

                if (status === "success") {
                    statusClass =
                        "history-status-success";
                }
                else if (status === "processing") {
                    statusClass =
                        "history-status-processing";
                }
                else if (status === "failed") {
                    statusClass =
                        "history-status-failed";
                }

                let durationText = "-";

                if (
                    item.duration_ms !== null &&
                    item.duration_ms !== undefined
                ) {

                    durationText =
                        (
                            Number(
                                item.duration_ms
                            ) / 1000
                        ).toFixed(2) +
                        " s";
                }

                let timeText =
                    item.created_at || "-";

                try {

                    timeText =
                        new Date(
                            item.created_at
                        ).toLocaleString(
                            "en-GB",
                            {
                                dateStyle:
                                    "medium",
                                timeStyle:
                                    "medium"
                            }
                        );

                }
                catch (timeError) {

                    timeText =
                        item.created_at || "-";
                }

                body.innerHTML +=

                    "<tr " +
                    "id='history-row-" +
                    rowId +
                    "' " +
                    "class='history-row' " +
                    "onclick=\"toggleHistoryRow('" +
                    rowId +
                    "')\">" +

                        "<td>" +
                            "<span class='history-chevron'>" +
                                "▶" +
                            "</span>" +
                        "</td>" +

                        "<td>" +
                            escapeHtml(item.id) +
                        "</td>" +

                        "<td>" +
                            escapeHtml(timeText) +
                        "</td>" +

                        "<td>" +
                            escapeHtml(
                                item.event_id || "-"
                            ) +
                        "</td>" +

                        "<td>" +
                            escapeHtml(
                                item.host || "-"
                            ) +
                        "</td>" +

                        "<td>" +
                            escapeHtml(
                                item.severity || "-"
                            ) +
                        "</td>" +

                        "<td>" +
                            escapeHtml(
                                item.problem || "-"
                            ) +
                        "</td>" +

                        "<td>" +

                            "<span " +
                            "class='history-status " +
                            statusClass +
                            "'>" +

                                escapeHtml(status) +

                            "</span>" +

                        "</td>" +

                        "<td>" +

                            "<span " +
                            "class='history-duration'>" +

                                escapeHtml(
                                    durationText
                                ) +

                            "</span>" +

                        "</td>" +

                    "</tr>" +

                    "<tr " +
                    "id='history-detail-" +
                    rowId +
                    "' " +
                    "class='history-detail-row'>" +

                        "<td " +
                        "colspan='9' " +
                        "class='history-detail-cell'>" +

                            "<div " +
                            "class='history-detail-grid'>" +

                                "<div class='history-detail-box'>" +

                                    "<div class='history-detail-label'>" +
                                        "Investigation ID" +
                                    "</div>" +

                                    "<div class='history-detail-value'>" +
                                        escapeHtml(
                                            item.id || "-"
                                        ) +
                                    "</div>" +

                                "</div>" +

                                "<div class='history-detail-box'>" +

                                    "<div class='history-detail-label'>" +
                                        "Event ID" +
                                    "</div>" +

                                    "<div class='history-detail-value'>" +
                                        escapeHtml(
                                            item.event_id || "-"
                                        ) +
                                    "</div>" +

                                "</div>" +

                                "<div class='history-detail-box'>" +

                                    "<div class='history-detail-label'>" +
                                        "Started" +
                                    "</div>" +

                                    "<div class='history-detail-value'>" +
                                        escapeHtml(
                                            item.started_at || "-"
                                        ) +
                                    "</div>" +

                                "</div>" +

                                "<div class='history-detail-box'>" +

                                    "<div class='history-detail-label'>" +
                                        "Completed" +
                                    "</div>" +

                                    "<div class='history-detail-value'>" +
                                        escapeHtml(
                                            item.completed_at || "-"
                                        ) +
                                    "</div>" +

                                "</div>" +

                            "</div>" +

                            "<div class='history-detail-box'>" +

                                "<div class='history-detail-label'>" +
                                    "AI Analysis" +
                                "</div>" +

                                "<div " +
                                "class='history-detail-analysis'>" +

                                    escapeHtml(
                                        cleanAIText(
                                            item.analysis || ""
                                        )
                                    ) +

                                "</div>" +

                            "</div>" +

                        "</td>" +

                    "</tr>";

            }
        );

    }
    catch (err) {

        body.innerHTML =
            "<tr><td colspan='9'>" +
            "Failed to load history: " +
            escapeHtml(err.message) +
            "</td></tr>";

    }
}

document
    .getElementById("questionInput")
    .addEventListener(
        "keydown",
        function(event){
            if(event.key==="Enter"){
                askAI();
            }
        }
    );


loadHistory();

</script>

</body>
</html>
'''


# ============================================================
# ROUTES
# ============================================================

@app.get(
    "/",
    response_class=HTMLResponse,
)
def root():
    return HTML_PAGE


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/analyze")
def analyze():

    try:

        result = run_agent(
            verbose=False
        )

        return {
            "status": "success",
            "monitored_hosts":
                result.get("monitored_hosts", []),
            "active_problems":
                result.get("active_problems", []),
            "cpu":
                result.get("cpu", []),
            "memory":
                result.get("memory", []),
            "hosts":
                result.get("hosts", []),
            "host_count":
                result.get("host_count", 0),
            "intent":
                result.get("intent"),
            "analysis":
                result.get("analysis", ""),
        }

    except Exception as e:

        return {
            "status": "error",
            "error": str(e),
        }


@app.post("/ask")
def ask_ai(
    request: AskRequest
):

    try:

        result = run_agent(
            question=request.question,
            output_mode=request.mode,
            verbose=False
        )

        return {
            "status": "success",
            "question": request.question,
            "answer": result,
        }

    except Exception as e:

        return {
            "status": "error",
            "error": str(e),
        }


@app.get("/investigations")
def investigations(
    limit: int = 50
):

    safe_limit = max(
        1,
        min(limit, 200)
    )

    items = get_investigations(
        safe_limit
    )

    return {
        "status": "success",
        "count": len(items),
        "items": items,
    }


@app.post("/zabbix-webhook")
def zabbix_webhook(
    request: ZabbixWebhookRequest,
    x_zabbix_token: str | None =
        Header(default=None),
):

    expected_token = os.environ.get(
        "ZABBIX_WEBHOOK_TOKEN"
    )

    if not expected_token:

        raise HTTPException(
            status_code=500,
            detail=
                "ZABBIX_WEBHOOK_TOKEN "
                "is not configured",
        )

    if x_zabbix_token != expected_token:

        raise HTTPException(
            status_code=401,
            detail=
                "Invalid webhook token",
        )

    # ========================================================
    # DUPLICATE EVENT PROTECTION
    # ========================================================

    existing = find_investigation_by_event(
        request.event_id
    )

    if existing:

        return {
            "status":
                "success",

            "event_id":
                request.event_id,

            "investigation_id":
                existing["id"],

            "state":
                existing["status"],

            "duplicate":
                True,
        }

    # ========================================================
    # CREATE INITIAL HISTORY RECORD
    # ========================================================

    started_dt = datetime.now(
        timezone.utc
    )

    started_at = started_dt.isoformat()

    investigation_id = save_investigation(
        event_id=
            request.event_id,

        host=
            request.host,

        problem=
            request.problem,

        severity=
            request.severity,

        trigger_id=
            request.trigger_id,

        status=
            "processing",

        analysis=
            "AI investigation started.",

        started_at=
            started_at,
    )

    # ========================================================
    # BUILD INVESTIGATION QUESTION
    # ========================================================

    question = f"""
Investigate the following Zabbix event.

This event was automatically generated
by the Zabbix monitoring system.

Event ID:
{request.event_id}

Host:
{request.host}

Problem:
{request.problem}

Severity:
{request.severity}

Trigger ID:
{request.trigger_id}

Perform a READ-ONLY infrastructure investigation.

Use the current Zabbix monitoring data as the
source of truth.

Determine:

1. The affected host.
2. The active problem.
3. Current CPU condition.
4. Current memory condition.
5. Whether the issue appears expected,
   potentially abnormal, or requires investigation.
6. The recommended next steps for the
   infrastructure engineer.

Do not perform remediation.

Do not claim to have checked logs,
configuration, package history, filesystem,
network or security information unless those
data are available from Zabbix.
"""

    # ========================================================
    # RUN AI INVESTIGATION
    # ========================================================

    try:

        result = run_agent(
            question =
                question,

            verbose =
                False
        )

        analysis = result.get(
            "analysis",
            ""
        )

        completed_dt = datetime.now(
            timezone.utc
        )

        completed_at = completed_dt.isoformat()

        duration_ms = int(
            (
                completed_dt -
                started_dt
            ).total_seconds() *
            1000
        )

        update_investigation(
            investigation_id =
                investigation_id,

            status =
                "success",

            analysis =
                analysis,

            completed_at =
                completed_at,

            duration_ms =
                duration_ms,
        )

        return {

            "status":
                "success",

            "event_id":
                request.event_id,

            "investigation_id":
                investigation_id,

            "host":
                request.host,

            "problem":
                request.problem,

            "severity":
                request.severity,

            "trigger_id":
                request.trigger_id,

            "analysis":
                analysis,

            "duration_ms":
                duration_ms,
        }

    except Exception as e:

        error_text = str(e)

        completed_dt = datetime.now(
            timezone.utc
        )

        completed_at = completed_dt.isoformat()

        duration_ms = int(
            (
                completed_dt -
                started_dt
            ).total_seconds() *
            1000
        )

        update_investigation(
            investigation_id =
                investigation_id,

            status =
                "failed",

            analysis =
                error_text,

            completed_at =
                completed_at,

            duration_ms =
                duration_ms,
        )

        return {

            "status":
                "error",

            "event_id":
                request.event_id,

            "investigation_id":
                investigation_id,

            "error":
                error_text,
        }

