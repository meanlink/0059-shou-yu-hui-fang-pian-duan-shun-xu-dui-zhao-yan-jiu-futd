import {h} from './base.js';
import {intro,stats} from './readout.js';
import {feedback,onSubmit,options} from './submit.js';
import {trials,read,write} from './replay_api.js';
import {picker,state,levels} from './trial_picker.js';
const decisions={adopt:'改用回放 B',keep:'保留回放 A',defer:'延后决定'};

function basisPanel(record,data) {
 const r=data.current;
 if(!r){
   return `<p class="callout">当前第 ${h(record.revision)} 轮尚无可签批的有效结果。${record.state==='revising'?'旧结果已因更正失效，须重新冻结并出结果后才能签新意见。':''}</p>`;
 }
 const statsLine=stats([['依据轮次','第 '+r.revision+' 轮'],['B 相对 A（分）',r.effect],['精确双侧 p',r.p_value],['可交换分配',r.permutations]]);
 const strata=(r.detail??[]).map(x=>`<li>${h(levels[x.level])}：A ${h(x.a)} 人 / B ${h(x.b)} 人，分差 ${h(x.effect)}</li>`).join('');
 return `<section class="band"><h2>当前签批依据（第 ${h(r.revision)} 轮）</h2>${statsLine}<ul>${strata}</ul>
  <p class="callout">该结果${r.valid?'当前有效，可据此签署教材意见':'已失效，不能据此签批'}</p></section>`;
}

function historyPanel(data) {
 const items=data.history.map(m=>`<article class="entry"><h2>${h(decisions[m.decision])}（第 ${h(m.revision)} 轮意见）</h2>
  <p>${h(m.rationale)}</p><p>签署人：${h(m.signed_by)}　时间：${h(m.signed_at)}</p>
  <p class="callout">当时依据：效应 ${h(m.effect)} 分，p=${h(m.p_value)}，置换 ${h(m.permutations)} 次；${m.valid?'该轮结果仍有效':'该轮结果已被后续更正取代（留档可查）'}</p></article>`).join('');
 return `<section class="band stack"><h2>历轮教材意见与当时依据</h2>${items||'<p class="callout">还没有已签署的教材意见。</p>'}</section>`;
}

export async function render(outlet,user) {
 const rows=await trials();
 outlet.innerHTML=`${intro('教材签批','仅当前修订轮次的有效结果可作为签批依据。版本 B 积极提升且证据达到 0.05 阈值时才可换版；更正后须重新冻结出结果才能签新意见，旧意见与当时成绩结果仍可查。')}
 <div class="toolrow">${picker(rows)}</div>
 <div class="record-head"></div>
 <div class="split"><section class="memo stack"></section><div class="form-slot"></div></div>
 <div class="history stack"></div>`;
 const select=outlet.querySelector('[name=trial]');
 async function draw(){
   if(!select.value)return;
   const record=rows.find(r=>r.code===select.value);
   const data=await read(select.value,'memo');
   outlet.querySelector('.record-head').innerHTML=
     `<p class="callout">当前状态：${h(state[record.state])}　·　当前修订轮次：第 ${h(record.revision)} 轮</p>`;
   outlet.querySelector('.memo').innerHTML=basisPanel(record,data);
   const slot=outlet.querySelector('.form-slot');
   if(user.role==='reviewer'&&record.state==='evaluated'){
     slot.innerHTML=`<form class="entry"><h2>记录编辑安排</h2><label>处理意见<select name="decision">${options(Object.entries(decisions))}</select></label>
      <label>复核理由<textarea name="rationale" required minlength="6" maxlength="200"></textarea></label><button>按第 ${h(record.revision)} 轮结果签署教材意见</button>${feedback}</form>`;
     onSubmit(slot.querySelector('form'),async entry=>{await write(select.value,'memo',entry);rows.splice(0,rows.length,...await trials());await draw();return '教材编辑意见已签署';});
   }else{
     slot.innerHTML=record.state==='evaluated'?'':'<p class="callout">当前轮次未出有效结果，暂不能签署新意见。</p>';
   }
   outlet.querySelector('.history').innerHTML=historyPanel(data);
 }
 select.onchange=draw;
 await draw();
}
