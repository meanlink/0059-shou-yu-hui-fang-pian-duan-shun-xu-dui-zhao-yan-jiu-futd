import {intro} from './readout.js';
import {feedback,onSubmit,options} from './submit.js';
import {trials,read,write} from './replay_api.js';
import {picker} from './trial_picker.js';
import {matrix} from './score_matrix.js';
export async function render(outlet,user) {
 const rows=await trials();
 outlet.innerHTML=`${intro('匿名试教','先核对码上的回放版本，再录入对应观测分数。数据按水平分层保留。')}<div class="toolrow">${picker(rows)}</div><div class="split"><div class="matrix stack band"></div>
 ${user.role==='operator'?`<form class="entry"><h2>核对后记分</h2><label>匿名码<select name="learner"></select></label><label>实际回放<select name="actual_arm"><option>A</option><option>B</option></select></label>
 <label>理解测试分<input name="score" type="number" min="0" max="100" required></label><button>保存成绩</button>${feedback}</form>`:'<p class="callout">在同一水平、同一版本内至少两个有效观测后再做置换。</p>'}</div>`;
 const select=outlet.querySelector('[name=trial]');
 async function draw(){
   if(!select.value)return;
   const roster=await read(select.value,'assignments');
   outlet.querySelector('.matrix').innerHTML=matrix(roster);
   if(outlet.querySelector('[name=learner]'))outlet.querySelector('[name=learner]').innerHTML=options(roster.map(r=>[r.learner,r.learner+' · '+r.arm]));
 }
 select.onchange=draw;
 onSubmit(outlet.querySelector('form'),async entry=>{await write(select.value,'scores',{...entry,score:+entry.score});await draw();return '匿名试教成绩已保存';});
 await draw();
}
