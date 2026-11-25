import {h} from './base.js';
import {intro} from './readout.js';
import {feedback,onSubmit,options} from './submit.js';
import {trials,read,write} from './replay_api.js';
import {picker} from './trial_picker.js';
const decisions={adopt:'改用回放 B',keep:'保留回放 A',defer:'延后决定'};
export async function render(outlet,user) {
 const rows=(await trials()).filter(r=>['evaluated','signed'].includes(r.state));
 outlet.innerHTML=`${intro('教材签批','版本 B 积极提升且证据达到 0.05 阈值时才可换版。保留原版本或延后也应记录编辑理由。')}<div class="toolrow">${picker(rows)}</div><div class="split"><section class="editor-note memo"></section>
 ${user.role==='reviewer'&&rows.length?`<form class="entry"><h2>记录编辑安排</h2><label>处理意见<select name="decision">${options(Object.entries(decisions))}</select></label>
 <label>复核理由<textarea name="rationale" required minlength="6"></textarea></label><button>签署教材意见</button>${feedback}</form>`:''}</div>`;
 const select=outlet.querySelector('[name=trial]');
 async function draw(){
   const memo=select.value ? await read(select.value,'memo') : null;
   outlet.querySelector('.memo').innerHTML=memo?`<h2>${h(decisions[memo.decision])}</h2><p>${h(memo.rationale)}</p><p>${h(memo.signed_by)}</p>`:'<p>没有已签编辑意见。</p>';
 }
 select.onchange=draw;
 onSubmit(outlet.querySelector('form'),async entry=>{await write(select.value,'memo',entry);await draw();return '教材编辑意见已签署';});
 await draw();
}
