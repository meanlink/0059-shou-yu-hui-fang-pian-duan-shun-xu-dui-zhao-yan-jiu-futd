import {h} from './base.js';
import {intro} from './readout.js';
import {feedback,onSubmit,options} from './submit.js';
import {trials,read,write,correct} from './replay_api.js';
import {picker,state} from './trial_picker.js';
import {matrix} from './score_matrix.js';

const correctable=new Set(['frozen','evaluated','signed']);

function correctionLog(data) {
 const items=data.corrections.map(c=>`<tr><td>第 ${h(c.revision)} 轮</td><td>${h(c.reason)}</td><td>${h(c.accepted_by)}</td><td>${h(c.accepted_at)}</td></tr>`).join('');
 const changes=data.score_history.map(s=>`<tr><td>${h(s.learner)}</td><td>${h(s.score)}</td><td>${h(s.actual_arm)}</td><td>第 ${h(s.revision)} 轮 · ${s.source==='register'?'登记':'更正'}</td><td>${h(s.changed_by)}</td><td>${h(s.changed_at)}</td></tr>`).join('');
 return `<section class="band stack"><h2>更正与成绩留痕</h2>
 <div class="data-frame"><table><caption>更正受理单</caption><thead><tr><th>受理时轮次</th><th>更正原因</th><th>受理人</th><th>时间</th></tr></thead><tbody>${items||'<tr><td colspan="4">暂无更正记录</td></tr>'}</tbody></table></div>
 <div class="data-frame"><table><caption>成绩变更流水</caption><thead><tr><th>匿名码</th><th>成绩</th><th>实际回放</th><th>轮次/来源</th><th>操作人</th><th>时间</th></tr></thead><tbody>${changes||'<tr><td colspan="6">暂无成绩记录</td></tr>'}</tbody></table></div></section>`;
}

export async function render(outlet,user) {
 const rows=await trials();
 const canCorrect=user.role==='reviewer';
 outlet.innerHTML=`${intro('匿名试教','先核对码上的回放版本，再录入对应观测分数。冻结后发现抄错分，由复核员在原试教登记上受理更正，旧结果随即失效。')}
 <div class="toolrow">${picker(rows)}</div>
 <div class="revision-callout"></div>
 <div class="split"><div class="matrix stack band"></div><div class="side stack"></div></div>
 <div class="history stack"></div>`;
 const select=outlet.querySelector('[name=trial]');
 async function draw(){
   if(!select.value)return;
   const record=rows.find(r=>r.code===select.value);
   const roster=await read(select.value,'assignments');
   outlet.querySelector('.matrix').innerHTML=matrix(roster);
   outlet.querySelector('.revision-callout').innerHTML=
     `<p class="callout">当前状态：${h(state[record.state])}　·　当前修订轮次：第 ${h(record.revision)} 轮${record.state==='revising'?'　·　旧结果已失效，重新冻结出结果后方可签批':''}</p>`;
   const side=outlet.querySelector('.side');
   if(user.role==='operator'&&record.state==='open'){
     side.innerHTML=`<form class="entry"><h2>核对后记分</h2><label>匿名码<select name="learner"></select></label><label>实际回放<select name="actual_arm"><option>A</option><option>B</option></select></label>
      <label>理解测试分<input name="score" type="number" min="0" max="100" required></label><button>保存成绩</button>${feedback}</form>`;
     side.querySelector('[name=learner]').innerHTML=options(roster.map(r=>[r.learner,r.learner+' · '+r.arm]));
     onSubmit(side.querySelector('form'),async entry=>{await write(select.value,'scores',{...entry,score:+entry.score});await draw();return '匿名试教成绩已保存';});
   }else if(canCorrect&&correctable.has(record.state)){
     side.innerHTML=`<form class="entry"><h2>受理成绩更正</h2><p class="callout">受理后当前第 ${h(record.revision)} 轮结果立即失效，需重新冻结计算。</p>
      <label>匿名码<select name="learner"></select></label><label>实际回放<select name="actual_arm"><option>A</option><option>B</option></select></label>
      <label>更正后成绩<input name="score" type="number" min="0" max="100" required></label>
      <label>更正原因<textarea name="reason" required minlength="6" maxlength="200"></textarea></label><button>受理更正并作废旧结果</button>${feedback}</form>`;
     side.querySelector('[name=learner]').innerHTML=options(roster.map(r=>[r.learner,`${r.learner} · ${r.arm} · 现 ${r.score??'无'}`]));
     onSubmit(side.querySelector('form'),async entry=>{await correct(select.value,{...entry,score:+entry.score});rows.splice(0,rows.length,...await trials());await draw();return '更正已受理，旧结果已失效';});
   }else if(record.state==='revising'){
     side.innerHTML='<p class="callout">成绩更正受理中。请复核员到「置换复核」页重新冻结并计算新一轮结果。</p>';
   }else{
     side.innerHTML='<p class="callout">试教冻结后成绩不可直接修改；如需更正，请由复核员受理。</p>';
   }
   outlet.querySelector('.history').innerHTML=correctionLog(await read(select.value,'corrections'));
 }
 select.onchange=draw;
 await draw();
}
