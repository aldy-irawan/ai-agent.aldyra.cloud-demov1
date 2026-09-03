import os
from datetime import datetime, timezone

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from action_manager import router as action_router
from agent_gemini import run_agent
from investigation_store import (
    find_investigation_by_event,
    get_investigations,
    init_db,
    save_investigation,
    update_investigation,
)

app = FastAPI(title="Zabbix AI Infrastructure Agent", description="AI monitoring analysis using Zabbix and Gemini", version="1.0")
app.include_router(action_router)
init_db()

class AskRequest(BaseModel):
    question: str
    mode: str = "simple"

class ZabbixWebhookRequest(BaseModel):
    event_id: str | None = None
    host: str | None = None
    problem: str | None = None
    severity: str | None = None
    trigger_id: str | None = None

HTML_PAGE = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zabbix AI Infrastructure Agent</title>
<style>
body{font-family:Arial;margin:0;background:#f4f6f8;color:#1f2937}.header{background:#111827;color:white;padding:22px 40px}.container{max-width:1150px;margin:30px auto;padding:0 20px}.card{background:white;padding:24px;border-radius:12px;margin-bottom:20px;box-shadow:0 2px 8px #0001}button{padding:12px 20px;border:0;border-radius:8px;background:#2563eb;color:white;font-weight:bold;cursor:pointer}button:disabled{background:#9ca3af}.stop{background:#dc2626}.cancel{background:#64748b}input{padding:12px;border:1px solid #d1d5db;border-radius:8px;font-size:15px}.row{display:flex;gap:10px}.row input{flex:1}.badge{padding:5px 10px;border-radius:15px;background:#ede9fe;color:#6d28d9;font-size:12px;font-weight:bold}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.box{background:#f8fafc;border:1px solid #e5e7eb;padding:16px;border-radius:8px}.label{font-size:11px;color:#64748b;text-transform:uppercase}.value{font-size:25px;font-weight:bold;margin-top:5px}.result{display:none}.loading,.error,.success{display:none;padding:14px;margin-top:12px;border-radius:8px}.loading{color:#64748b}.error{background:#fee2e2;color:#991b1b}.success{background:#f0fdf4;color:#166534}.proposal{display:none;background:#fffbeb;border:2px solid #fed7aa;padding:18px;border-radius:10px;margin-top:15px}.ai-recommendation{display:none;background:#f8fafc;border:1px solid #dbeafe;padding:18px;border-radius:10px;margin-top:15px}.ai-recommendation-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:15px 0}.recommendation-action{font-size:18px;font-weight:bold}.recommendation-reason{background:white;border:1px solid #e5e7eb;padding:14px;border-radius:8px;margin-top:10px;line-height:1.5}.recommendation-evidence{margin:8px 0 0 20px;padding-left:18px}.markdown{line-height:1.65;font-size:15px;word-break:normal;overflow-wrap:anywhere}.markdown h1,.markdown h2,.markdown h3{margin:22px 0 10px;color:#111827}.markdown h2{font-size:20px;border-bottom:1px solid #e5e7eb;padding-bottom:7px}.markdown h3{font-size:17px}.markdown p{margin:9px 0}.markdown ul,.markdown ol{margin:8px 0 14px 24px}.markdown li{margin:6px 0}.markdown code{background:#f3f4f6;padding:2px 5px;border-radius:4px;font-family:Consolas,monospace}.markdown pre{background:#111827;color:#f9fafb;padding:14px;border-radius:8px;overflow:auto}.markdown hr{border:0;border-top:1px solid #e5e7eb;margin:18px 0}.history-table th,.history-table td{vertical-align:middle}.history-table{min-width:1050px}.history-toggle{padding:7px 11px;font-size:12px;background:#64748b;min-width:82px}.history-detail-row{display:none}.history-detail-cell{background:#f8fafc;padding:0!important}.history-detail{padding:18px 22px;border-left:3px solid #cbd5e1}.history-detail .markdown{font-size:14px}.proposal-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:15px 0}table{width:100%;border-collapse:collapse}th,td{padding:10px;border-bottom:1px solid #e5e7eb;text-align:left}th{background:#f8fafc;font-size:12px}@media(max-width:800px){.grid,.proposal-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.grid,.proposal-grid{grid-template-columns:1fr}.row{flex-direction:column}}
.ai-section{border:1px solid #e5e7eb;border-radius:10px;margin:0 0 12px;overflow:hidden;background:#fff}.ai-section-header{width:100%;display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border:0;border-bottom:1px solid transparent;background:#f8fafc;color:#111827;font-size:15px;font-weight:700;text-align:left;cursor:pointer}.ai-section-header:hover{background:#f1f5f9}.ai-section.open .ai-section-header{border-bottom-color:#e5e7eb}.ai-section-body{display:none;padding:16px 18px}.ai-section.open .ai-section-body{display:block}.ai-chevron{transition:transform .15s ease;font-size:12px}.ai-section.open>.ai-section-header .ai-chevron{transform:rotate(90deg)}.ai-host-section{border:1px solid #e5e7eb;border-radius:8px;margin:0 0 8px;overflow:hidden}.ai-host-header{width:100%;display:flex;justify-content:space-between;align-items:center;padding:11px 13px;border:0;background:#fafafa;color:#1f2937;font-size:14px;font-weight:700;text-align:left;cursor:pointer}.ai-host-header:hover{background:#f3f4f6}.ai-host-body{display:none;padding:13px;border-top:1px solid #e5e7eb}.ai-host-section.open .ai-host-body{display:block}.ai-host-section.open .ai-chevron{transform:rotate(90deg)}.ai-analysis-empty{color:#64748b;font-style:italic}</style></head><body>
<div class="header"><h1>Zabbix AI Infrastructure Agent</h1><p>AI-powered infrastructure investigation using Zabbix + Gemini</p></div>
<div class="container">
<div class="card"><h2>Infrastructure Monitoring <span class="badge">READY</span></h2><p>Monitoring Source: <b>Zabbix</b></p><p>AI Engine: <b>Google Gemini</b></p><p>Action Control: <b>Human confirmation required</b></p></div>
<div class="card"><button id="analyzeButton" onclick="runAnalysis()">🔍 RUN AI ANALYSIS</button><div id="loading" class="loading">🤖 AI is investigating...</div><div id="error" class="error"></div></div>
<div id="summaryCard" class="card result"><h2>Infrastructure Summary</h2><div class="grid"><div class="box"><div class="label">Monitored Hosts</div><div id="hostCount" class="value">0</div></div><div class="box"><div class="label">Active Problems</div><div id="problemCount" class="value">0</div></div><div class="box"><div class="label">Highest CPU</div><div id="highestCPU" class="value">-</div></div><div class="box"><div class="label">Highest Memory</div><div id="highestMemory" class="value">-</div></div></div></div>
<div id="hostsCard" class="card result"><h2>Monitored Hosts</h2><table><thead><tr><th>Host</th><th>Status</th><th>Problems</th><th>CPU</th><th>Memory</th></tr></thead><tbody id="hostTableBody"></tbody></table></div>
<div id="problemsCard" class="card result"><h2>Active Problems</h2><div id="problemsContainer"></div></div>
<div id="analysisCard" class="card result"><h2>AI Analysis <span class="badge">GEMINI AI</span></h2><div id="analysisText" class="markdown"></div></div>
<div id="recommendationCard" class="card result">
<h2>🤖 AI Recommended Action <span class="badge">HUMAN APPROVAL</span></h2>
<p>AI has identified a state-changing action that requires explicit human confirmation.</p>
<div id="recommendationBox" class="ai-recommendation">
<div class="ai-recommendation-grid">
<div class="box"><div class="label">Recommended Action</div><div id="rAction" class="recommendation-action">STOP</div></div>
<div class="box"><div class="label">Target Instance</div><div id="rHost">-</div></div>
<div class="box"><div class="label">Decision</div><div id="rDecision">REVIEW</div></div>
<div class="box"><div class="label">Evidence Count</div><div id="rEvidenceCount">0</div></div>
</div>
<div class="label">Reason</div>
<div id="rReason" class="recommendation-reason"></div>
<div id="evidenceWrap" style="display:none;margin-top:14px"><div class="label">Evidence</div><ul id="rEvidence" class="recommendation-evidence"></ul></div>
<button id="proposeAiButton" class="stop" style="display:none;margin-top:14px" onclick="proposeAiAction()">🛑 PROPOSE AI RECOMMENDED STOP</button>
</div>
</div>
<div class="card"><h2>Ask AI Infrastructure Assistant <span class="badge">GEMINI AI</span></h2><div class="row"><input id="questionInput" placeholder="Example: Which server has the highest CPU?" onkeydown="if(event.key==='Enter')askAI()"><button onclick="askAI()">🤖 ASK AI</button></div><div id="askLoading" class="loading">🤖 AI is analyzing...</div><div id="askError" class="error"></div><div id="askResult" class="card result"><div id="answerText" class="markdown"></div></div></div>
<div class="card"><h2>Investigation History <span class="badge">AI HISTORY</span></h2><table class="history-table"><thead><tr><th>ID</th><th>Time</th><th>Event</th><th>Host</th><th>Severity</th><th>Problem</th><th>Status</th><th>Duration</th><th>Details</th></tr></thead><tbody id="historyTableBody"><tr><td colspan="9">Loading...</td></tr></tbody></table></div>
</div>
<script>
let proposalId=null;

const esc=v=>String(v??'')
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;')
    .replace(/'/g,'&#039;');

/* ---------------------------------------------------------
   Lightweight Markdown renderer for Gemini output.
   We intentionally render only safe, supported Markdown
   constructs and escape all HTML first.
--------------------------------------------------------- */
function renderMarkdown(value, hostNames=[]){
    if(value===null || value===undefined) return '';

    let text=String(value).replace(/\r\n/g,'\n').replace(/\r/g,'\n');
    let lines=text.split('\n');
    let html='';
    let inUl=false;
    let inOl=false;
    let inCode=false;
    let codeBuffer=[];

    function closeLists(){
        if(inUl){ html+='</ul>'; inUl=false; }
        if(inOl){ html+='</ol>'; inOl=false; }
    }
    function inlineMarkdown(s){
        s=esc(s);
        s=s.replace(/`([^`]+)`/g,'<code>$1</code>');
        s=s.replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>');
        s=s.replace(/__([^_]+)__/g,'<strong>$1</strong>');
        s=s.replace(/\*([^*]+)\*/g,'<em>$1</em>');
        s=s.replace(/_([^_]+)_/g,'<em>$1</em>');
        return s;
    }
    for(let i=0;i<lines.length;i++){
        const raw=lines[i];
        if(raw.trim().startsWith('```')){
            if(!inCode){closeLists();inCode=true;codeBuffer=[];}
            else{html+='<pre>'+esc(codeBuffer.join('\n'))+'</pre>';inCode=false;codeBuffer=[];}
            continue;
        }
        if(inCode){codeBuffer.push(raw);continue;}
        const line=raw.trim();
        if(!line){closeLists();continue;}
        if(/^(-{3,}|\*{3,}|_{3,})$/.test(line)){closeLists();html+='<hr>';continue;}
        let m=line.match(/^###\s+(.+)$/);
        if(m){closeLists();html+='<h3>'+inlineMarkdown(m[1])+'</h3>';continue;}
        m=line.match(/^##\s+(.+)$/);
        if(m){closeLists();html+='<h2>'+inlineMarkdown(m[1])+'</h2>';continue;}
        m=line.match(/^#\s+(.+)$/);
        if(m){closeLists();html+='<h2>'+inlineMarkdown(m[1])+'</h2>';continue;}
        m=line.match(/^[-*]\s+(.+)$/);
        if(m){if(inOl){html+='</ol>';inOl=false;}if(!inUl){html+='<ul>';inUl=true;}html+='<li>'+inlineMarkdown(m[1])+'</li>';continue;}
        m=line.match(/^\d+\.\s+(.+)$/);
        if(m){if(inUl){html+='</ul>';inUl=false;}if(!inOl){html+='<ol>';inOl=true;}html+='<li>'+inlineMarkdown(m[1])+'</li>';continue;}
        closeLists();
        html+='<p>'+inlineMarkdown(line)+'</p>';
    }
    if(inCode)html+='<pre>'+esc(codeBuffer.join('\n'))+'</pre>';
    closeLists();
    return buildCollapsibleAnalysis(html,hostNames);
}

function toggleAiSection(id){
    const el=document.getElementById(id);
    if(!el)return;

    el.classList.toggle('open');
}

function toggleAiHost(id){
    const el=document.getElementById(id);
    if(!el)return;

    el.classList.toggle('open');
}

function sectionIcon(title){
    const t=String(title).toLowerCase();
    if(t.includes('monitoring summary'))return '📊';
    if(t.includes('host-by-host'))return '🖥️';
    if(t.includes('active incident'))return '🚨';
    if(t.includes('correlation'))return '🔗';
    if(t.includes('comparative'))return '⚖️';
    if(t.includes('likely explanation'))return '💡';
    if(t.includes('recommended next steps'))return '➡️';
    return '📋';
}

function buildCollapsibleAnalysis(html,hostNames=[]){
    const temp=document.createElement('div');
    temp.innerHTML=html;
    const heads=Array.from(temp.querySelectorAll('h3')).filter(h=>/^\d+\.\s+/.test(h.textContent.trim()));
    if(!heads.length)return html;

    let out='';
    heads.forEach((head,idx)=>{
        const id='ai-section-'+(idx+1);
        const title=head.textContent.trim();
        const body=document.createElement('div');
        let node=head.nextSibling;
        while(node && node!==heads[idx+1]){
            const next=node.nextSibling;
            body.appendChild(node);
            node=next;
        }
        let bodyHtml=body.innerHTML;
        if(/host-by-host assessment/i.test(title)){
            bodyHtml=buildHostAccordions(bodyHtml,hostNames);
        }
        out+='<div id="'+id+'" class="ai-section">'+
             '<button type="button" class="ai-section-header" onclick="toggleAiSection(\''+id+'\')">'+
             '<span>'+sectionIcon(title)+' '+esc(title.replace(/^\d+\.\s*/,''))+'</span><span class="ai-chevron">▶</span></button>'+
             '<div class="ai-section-body">'+bodyHtml+'</div></div>';
    });
    return out;
}

function buildHostAccordions(bodyHtml,hostNames=[]){
    const temp=document.createElement('div');
    temp.innerHTML=bodyHtml;
    const names=(Array.isArray(hostNames)?hostNames:[]).map(x=>String(x.name||x.host||x).trim()).filter(Boolean);
    if(!names.length)return bodyHtml;

    const children=Array.from(temp.children);
    let blocks=[];
    names.forEach(name=>{
        const idx=children.findIndex(n=>new RegExp('^'+escapeRegex(name)+'\\b','i').test(n.textContent.trim()) || new RegExp('^Host\\s*:\\s*'+escapeRegex(name)+'\\b','i').test(n.textContent.trim()));
        blocks.push({name,idx});
    });
    const valid=blocks.filter(x=>x.idx>=0).sort((a,b)=>a.idx-b.idx);
    if(!valid.length)return bodyHtml;

    let out='';
    valid.forEach((b,i)=>{
        const next=valid[i+1]?.idx ?? children.length;
        let content='';
        for(let j=b.idx;j<next;j++)content+=children[j].outerHTML||'';
        const id='ai-host-'+(i+1);
        out+='<div id="'+id+'" class="ai-host-section">'+
             '<button type="button" class="ai-host-header" onclick="toggleAiHost(\''+id+'\')">'+
             '<span>🖥️ '+esc(b.name)+'</span><span class="ai-chevron">▶</span></button>'+
             '<div class="ai-host-body">'+content+'</div></div>';
    });
    return out;
}

function escapeRegex(value){return String(value).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');}

function showRecommendation(rec){
    const card=document.getElementById('recommendationCard');
    const box=document.getElementById('recommendationBox');

    /* Do not show any action UI unless AI explicitly recommends STOP.
       The normal state-changing flow remains behind the Action Manager
       proposal + human confirmation endpoints. */
    if(!rec || rec.recommended_action!=='stop' || !rec.instance_name){
        card.style.display='none';
        box.style.display='none';
        return;
    }

    card.style.display='block';
    box.style.display='block';

    rAction.textContent=String(rec.recommended_action||'none').toUpperCase();
    rHost.textContent=rec.instance_name||'-';
    rDecision.textContent=rec.decision||'REVIEW';
    rReason.textContent=rec.reason||'No reason supplied.';

    const evidence=Array.isArray(rec.evidence)?rec.evidence:[];
    rEvidenceCount.textContent=evidence.length;

    if(evidence.length){
        rEvidence.innerHTML=evidence.map(x=>'<li>'+esc(x)+'</li>').join('');
        evidenceWrap.style.display='block';
    }else{
        rEvidence.innerHTML='';
        evidenceWrap.style.display='none';
    }

    /* The STOP button exists only when AI recommends STOP. */
    proposeAiButton.style.display='inline-block';
}

async function runAnalysis(){
    const b=document.getElementById('analyzeButton');
    const l=document.getElementById('loading');
    const e=document.getElementById('error');

    b.disabled=true;
    b.textContent='⏳ ANALYZING...';
    l.style.display='block';
    e.style.display='none';

    try{
        const r=await fetch('/analyze');
        const d=await r.json();

        if(!r.ok || d.status!=='success')
            throw Error(d.error||'Analysis failed');

        const h=d.monitored_hosts||[];
        const p=d.active_problems||[];
        const c=d.cpu||[];
        const m=d.memory||[];

        hostCount.textContent=h.length;
        problemCount.textContent=p.length;

        highestCPU.textContent=c.length
            ? Number([...c].sort((a,b)=>+b.value-+a.value)[0].value).toFixed(2)+'%'
            : 'N/A';

        highestMemory.textContent=m.length
            ? Number([...m].sort((a,b)=>+b.value-+a.value)[0].value).toFixed(2)+'%'
            : 'N/A';

        let map={};

        h.forEach(x=>{
            let n=x.name||x.host;
            if(n) map[n]={name:n,status:x.status,problems:[],cpu:null,memory:null};
        });

        p.forEach(x=>{
            if(x.host){
                if(!map[x.host])
                    map[x.host]={name:x.host,status:null,problems:[],cpu:null,memory:null};
                map[x.host].problems.push(x);
            }
        });

        c.forEach(x=>{
            if(x.host){
                if(!map[x.host])
                    map[x.host]={name:x.host,status:null,problems:[],cpu:null,memory:null};
                map[x.host].cpu=x;
            }
        });

        m.forEach(x=>{
            if(x.host){
                if(!map[x.host])
                    map[x.host]={name:x.host,status:null,problems:[],cpu:null,memory:null};
                map[x.host].memory=x;
            }
        });

        hostTableBody.innerHTML=Object.values(map).map(x=>
            '<tr><td>'+esc(x.name)+'</td>'+
            '<td>'+esc(x.status==='0'?'Enabled':x.status==='1'?'Disabled':'N/A')+'</td>'+
            '<td>'+x.problems.length+'</td>'+
            '<td>'+(x.cpu?Number(x.cpu.value).toFixed(2)+'%':'N/A')+'</td>'+
            '<td>'+(x.memory?Number(x.memory.value).toFixed(2)+'%':'N/A')+'</td></tr>'
        ).join('');

        problemsContainer.innerHTML=p.length
            ? p.map(x=>
                '<div class="box"><b>⚠️ '+esc(x.problem)+'</b><br>'+
                'Host: '+esc(x.host)+'<br>'+
                'Severity: '+esc(x.severity)+'</div>'
              ).join('')
            : '<div class="box">🟢 No Active Problems</div>';

        /* FIX: Gemini Markdown is rendered as HTML instead of
           being displayed literally with ## and **. */
        analysisText.innerHTML=renderMarkdown(d.analysis||'',h);

        ['summaryCard','hostsCard','problemsCard','analysisCard']
            .forEach(id=>document.getElementById(id).style.display='block');

        showRecommendation(d.action_recommendation||{});

    }catch(x){
        e.textContent='Error: '+x.message;
        e.style.display='block';
    }finally{
        b.disabled=false;
        b.textContent='🔍 RUN AI ANALYSIS';
        l.style.display='none';
    }
}

async function askAI(){
    const q=questionInput.value.trim();

    if(!q){
        askError.textContent='Please enter a question.';
        askError.style.display='block';
        return;
    }

    askError.style.display='none';
    askLoading.style.display='block';
    askResult.style.display='none';

    try{
        const r=await fetch('/ask',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({question:q,mode:'simple'})
        });

        const d=await r.json();

        if(!r.ok || d.status!=='success')
            throw Error(d.error||'AI request failed');

        const answer=typeof d.answer==='object'
            ? (d.answer.analysis||JSON.stringify(d.answer,null,2))
            : d.answer;

        /* Also render Markdown in Ask AI output. */
        answerText.innerHTML=renderMarkdown(answer||[],[]);
        askResult.style.display='block';

    }catch(x){
        askError.textContent='Error: '+x.message;
        askError.style.display='block';
    }finally{
        askLoading.style.display='none';
    }
}

async function proposeAiAction(){
    const host=document.getElementById('rHost').textContent.trim();

    if(!host || host==='-'){
        showUiError('AI did not provide a valid target host.');
        return;
    }

    await createStopProposal(host);
}

function showUiError(message){
    let e=document.getElementById('aiActionError');
    if(!e){
        e=document.createElement('div');
        e.id='aiActionError';
        e.className='error';
        document.getElementById('recommendationBox').appendChild(e);
    }
    e.textContent='Error: '+message;
    e.style.display='block';
}

async function createStopProposal(instanceName){
    const box=document.getElementById('recommendationBox');
    const button=document.getElementById('proposeAiButton');

    let loading=document.getElementById('aiActionLoading');
    if(!loading){
        loading=document.createElement('div');
        loading.id='aiActionLoading';
        loading.className='loading';
        loading.textContent='🔎 Checking EC2 before proposal...';
        box.appendChild(loading);
    }

    let proposal=document.getElementById('aiProposalBox');
    if(proposal) proposal.remove();

    loading.style.display='block';
    button.disabled=true;
    button.textContent='⏳ CHECKING...';

    try{
        const r=await fetch('/action/propose',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
                action:'stop',
                instance_name:instanceName
            })
        });

        const d=await r.json();

        if(!r.ok || d.status!=='success')
            throw Error(d.detail||d.message||'Proposal rejected');

        proposalId=d.proposal_id;

        proposal=document.createElement('div');
        proposal.id='aiProposalBox';
        proposal.className='proposal';
        proposal.innerHTML=
            '<h3>⚠️ Action Confirmation Required</h3>'+
            '<div class="proposal-grid">'+
            '<div class="box"><div class="label">Action</div><div>'+esc((d.action||'stop').toUpperCase())+'</div></div>'+
            '<div class="box"><div class="label">Instance</div><div>'+esc(d.instance_name||'-')+'</div></div>'+
            '<div class="box"><div class="label">Instance ID</div><div>'+esc(d.instance_id||'-')+'</div></div>'+
            '<div class="box"><div class="label">Region</div><div>'+esc(d.region||'-')+'</div></div>'+
            '<div class="box"><div class="label">State</div><div>'+esc(d.current_state||'-')+'</div></div>'+
            '<div class="box"><div class="label">Type</div><div>'+esc(d.instance_type||'-')+'</div></div>'+
            '<div class="box"><div class="label">Private IP</div><div>'+esc(d.private_ip||'-')+'</div></div>'+
            '<div class="box"><div class="label">Decision</div><div>'+esc(d.decision||'-')+'</div></div>'+
            '</div>'+
            '<button id="confirmButton" class="stop" onclick="confirmStop()">✅ CONFIRM STOP</button> '+
            '<button class="cancel" onclick="cancelProposal()">CANCEL</button>'+
            '<div id="actionSuccess" class="success"></div>'+
            '<div id="actionFailed" class="error"></div>';

        box.appendChild(proposal);
        proposal.style.display='block';
        proposal.scrollIntoView({behavior:'smooth',block:'center'});

    }catch(x){
        showUiError(x.message);
    }finally{
        loading.style.display='none';
        button.disabled=false;
        button.textContent='🛑 PROPOSE AI RECOMMENDED STOP';
    }
}

async function confirmStop(){
    if(!proposalId){
        showUiError('No active proposal.');
        return;
    }

    const proposal=document.getElementById('aiProposalBox');
    const confirmButton=document.getElementById('confirmButton');
    const success=document.getElementById('actionSuccess');
    const failed=document.getElementById('actionFailed');

    confirmButton.disabled=true;
    confirmButton.textContent='⏳ EXECUTING...';

    try{
        const r=await fetch('/action/confirm',{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({proposal_id:proposalId})
        });

        const d=await r.json();

        if(!r.ok || d.status!=='success' || d.execution_status!=='executed')
            throw Error(d.detail||d.message||'Action failed');

        success.innerHTML=
            '<b>✅ ACTION COMPLETED</b><br>'+
            'Instance: '+esc(d.instance_name)+'<br>'+
            'Action: STOP<br>'+
            'Verified State: '+esc(d.verified_state||'stopped');

        success.style.display='block';
        confirmButton.style.display='none';
        proposal.querySelector('.cancel').style.display='none';
        proposalId=null;

        loadHistory();

    }catch(x){
        failed.textContent='❌ ACTION FAILED: '+x.message;
        failed.style.display='block';
        confirmButton.disabled=false;
        confirmButton.textContent='✅ CONFIRM STOP';
    }
}

function cancelProposal(){
    proposalId=null;
    const proposal=document.getElementById('aiProposalBox');
    if(proposal) proposal.remove();
}
function toggleHistory(id){
    const row=document.getElementById('history-detail-'+id);
    const btn=document.getElementById('history-toggle-'+id);
    if(!row || !btn) return;

    const open=row.style.display==='table-row';
    row.style.display=open?'none':'table-row';
    btn.textContent=open?'▶ VIEW':'▼ HIDE';
}

document.addEventListener('click',function(e){
    const btn=e.target.closest('.history-toggle');
    if(!btn) return;
    const id=btn.getAttribute('data-history-id');
    if(id!==null) toggleHistory(id);
});

async function loadHistory(){
    try{
        const r=await fetch('/investigations?limit=50');
        const d=await r.json();

        if(!d.items?.length){
            historyTableBody.innerHTML=
                '<tr><td colspan="9">No investigation history yet.</td></tr>';
            return;
        }

        historyTableBody.innerHTML=d.items.map(x=>{
            const id=esc(x.id);
            const detailId='history-detail-'+id;
            const analysis=x.analysis||'No investigation analysis stored.';
            const trigger=x.trigger_id||'-';
            const completed=x.completed_at||'-';

            return (
                '<tr>'+
                '<td>'+id+'</td>'+
                '<td>'+esc(x.created_at||'-')+'</td>'+
                '<td>'+esc(x.event_id||'-')+'</td>'+
                '<td>'+esc(x.host||'-')+'</td>'+
                '<td>'+esc(x.severity||'-')+'</td>'+
                '<td>'+esc(x.problem||'-')+'</td>'+
                '<td>'+esc(x.status||'-')+'</td>'+
                '<td>'+(x.duration_ms!=null?(Number(x.duration_ms)/1000).toFixed(2)+' s':'-')+'</td>'+
                '<td><button type="button" id="history-toggle-'+id+'" class="history-toggle" data-history-id="'+id+'">▶ VIEW</button></td>'+
                '</tr>'+
                '<tr id="'+detailId+'" class="history-detail-row">'+
                '<td colspan="9" class="history-detail-cell">'+
                '<div class="history-detail">'+
                '<div class="proposal-grid">'+
                '<div class="box"><div class="label">Event ID</div><div>'+esc(x.event_id||'-')+'</div></div>'+
                '<div class="box"><div class="label">Trigger ID</div><div>'+esc(trigger)+'</div></div>'+
                '<div class="box"><div class="label">Started</div><div>'+esc(x.created_at||'-')+'</div></div>'+
                '<div class="box"><div class="label">Completed</div><div>'+esc(completed)+'</div></div>'+
                '</div>'+
                '<div class="label">AI Investigation</div>'+
                '<div class="markdown">'+renderMarkdown(analysis)+'</div>'+
                '</div>'+
                '</td>'+
                '</tr>'
            );
        }).join('');

    }catch(x){
        historyTableBody.innerHTML=
            '<tr><td colspan="9">'+esc(x.message)+'</td></tr>';
    }
}

document.addEventListener('DOMContentLoaded',loadHistory);
</script></body></html>'''

@app.get('/', response_class=HTMLResponse)
def root(): return HTML_PAGE

@app.get('/health')
def health(): return {'status':'healthy'}

@app.get('/analyze')
def analyze():
    try:
        r=run_agent(verbose=False)
        return {'status':'success','monitored_hosts':r.get('monitored_hosts',[]),'active_problems':r.get('active_problems',[]),'cpu':r.get('cpu',[]),'memory':r.get('memory',[]),'hosts':r.get('hosts',[]),'host_count':r.get('host_count',0),'intent':r.get('intent'),'analysis':r.get('analysis',''),'action_recommendation':r.get('action_recommendation',{})}
    except Exception as e: return {'status':'error','error':str(e)}

@app.post('/ask')
def ask_ai(request:AskRequest):
    try:
        r=run_agent(question=request.question,output_mode=request.mode,verbose=False)
        return {'status':'success','question':request.question,'answer':r}
    except Exception as e: return {'status':'error','error':str(e)}

@app.get('/investigations')
def investigations(limit:int=50):
    items=get_investigations(max(1,min(limit,200)))
    return {'status':'success','count':len(items),'items':items}

@app.post('/zabbix-webhook')
def zabbix_webhook(request:ZabbixWebhookRequest,x_zabbix_token:str|None=Header(default=None)):
    expected=os.environ.get('ZABBIX_WEBHOOK_TOKEN')
    if not expected: raise HTTPException(status_code=500,detail='ZABBIX_WEBHOOK_TOKEN is not configured')
    if x_zabbix_token!=expected: raise HTTPException(status_code=401,detail='Invalid webhook token')
    existing=find_investigation_by_event(request.event_id)
    if existing: return {'status':'success','event_id':request.event_id,'investigation_id':existing['id'],'state':existing['status'],'duplicate':True}
    started=datetime.now(timezone.utc)
    iid=save_investigation(event_id=request.event_id,host=request.host,problem=request.problem,severity=request.severity,trigger_id=request.trigger_id,status='processing',analysis='AI investigation started.',started_at=started.isoformat())
    q='Investigate this Zabbix event using current Zabbix data only. Event ID: %s Host: %s Problem: %s Severity: %s Trigger ID: %s. Perform READ-ONLY investigation. Do not perform remediation.'%(request.event_id,request.host,request.problem,request.severity,request.trigger_id)
    try:
        r=run_agent(question=q,verbose=False);analysis=r.get('analysis','');done=datetime.now(timezone.utc);ms=int((done-started).total_seconds()*1000)
        update_investigation(investigation_id=iid,status='success',analysis=analysis,completed_at=done.isoformat(),duration_ms=ms)
        return {'status':'success','event_id':request.event_id,'investigation_id':iid,'host':request.host,'problem':request.problem,'severity':request.severity,'trigger_id':request.trigger_id,'analysis':analysis,'duration_ms':ms}
    except Exception as e:
        done=datetime.now(timezone.utc);ms=int((done-started).total_seconds()*1000)
        update_investigation(investigation_id=iid,status='failed',analysis=str(e),completed_at=done.isoformat(),duration_ms=ms)
        return {'status':'error','event_id':request.event_id,'investigation_id':iid,'error':str(e)}
