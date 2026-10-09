"""Static same-origin local dashboard; token stays in memory and DOM text is escaped."""

HTML = """<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RedBlue Arena — лаборатория</title>
<style>
body{font:16px system-ui;background:#101826;color:#e5edf7;max-width:1000px;margin:40px auto;padding:20px}
section{background:#1d293a;padding:24px;margin:20px 0;border-radius:12px}
input,select,button{padding:10px;margin:5px;background:#253950;color:white;border:1px solid #56708d;border-radius:6px}
button{cursor:pointer} pre{white-space:pre-wrap;overflow-wrap:anywhere}label{display:block} table{width:100%;text-align:left}td{padding:8px}
</style><h1>RedBlue Arena</h1><p>Только синтетические задания в авторизованной локальной лаборатории.</p>
<section><h2>Доступ</h2><label>Токен <input id="token" type="password" autocomplete="off"></label>
<button id="connect">Подключиться</button><button id="logout">Выйти</button><p id="identity">Не подключено</p></section>
<section><h2>Новое задание</h2><label>Учебная цель <input id="target" value="lab://training"></label>
<label>Сценарий <select id="scenario"><option>failed-logins</option><option>threshold-logins</option><option>benign-logins</option><option>spread-logins</option></select></label>
<label><input id="confirm" type="checkbox">Подтверждаю разрешение и scope этой лаборатории</label>
<button id="submit" disabled>Запустить</button></section>
<section><h2>Задания</h2><button id="refresh">Обновить</button><table><thead><tr><th>ID</th><th>Статус</th><th>Действия</th></tr></thead><tbody id="jobs"></tbody></table></section>
<section><h2>Отчёт</h2><pre id="report">Выберите задание</pre></section>
<section><h2>Аудит и хранение</h2><button id="audit" disabled>Проверить аудит</button><button id="prune" disabled>Очистить устаревшие отчёты</button><pre id="audit-report"></pre></section>
<p id="message" role="status"></p><script src="/app.js" defer></script></html>"""

JAVASCRIPT = """'use strict';
let token=''; const el=id=>document.getElementById(id);
async function api(path, method='GET', body){
 const r=await fetch(path,{method,headers:{'Authorization':'Bearer '+token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined});
 const data=await r.json(); if(!r.ok)throw Error(data.error||'Ошибка запроса'); return data;
}
function guarded(fn){return async()=>{try{el('message').textContent='';await fn();}catch(e){el('message').textContent=e.message;}};}
async function refresh(){const data=await api('/api/jobs');el('jobs').replaceChildren();
 for(const j of data.jobs){const row=document.createElement('tr');for(const v of [j.id,j.status]){const td=document.createElement('td');td.textContent=v;row.append(td);}const td=document.createElement('td');
 const view=document.createElement('button');view.textContent='Отчёт';view.onclick=guarded(async()=>{el('report').textContent=JSON.stringify(await api('/api/jobs/'+j.id),null,2);});td.append(view);
 if(['queued','running'].includes(j.status)){const cancel=document.createElement('button');cancel.textContent='Остановить';cancel.onclick=guarded(async()=>{await api('/api/jobs/'+j.id+'/cancel','POST',{});await refresh();});td.append(cancel);}row.append(td);el('jobs').append(row);}}
el('connect').onclick=guarded(async()=>{token=el('token').value;el('token').value='';const me=await api('/api/me');el('identity').textContent=me.tenant+' / '+me.subject+' / '+me.role+' / '+me.runner;el('submit').disabled=me.role==='viewer';el('audit').disabled=el('prune').disabled=me.role!=='admin';await refresh();});
el('logout').onclick=()=>{token='';el('token').value='';el('identity').textContent='Не подключено';el('jobs').replaceChildren();el('report').textContent='';el('audit-report').textContent='';el('submit').disabled=el('audit').disabled=el('prune').disabled=true;};
el('submit').onclick=guarded(async()=>{const target=el('target').value;await api('/api/jobs','POST',{config:{authorized:true,allowed_targets:[target],target,scenario:el('scenario').value},scope_confirmed:el('confirm').checked});el('confirm').checked=false;await refresh();});
el('refresh').onclick=guarded(refresh);el('audit').onclick=guarded(async()=>{el('audit-report').textContent=JSON.stringify(await api('/api/audit'),null,2);});
el('prune').onclick=guarded(async()=>{el('audit-report').textContent=JSON.stringify(await api('/api/retention/prune','POST',{}),null,2);});
"""
