import {intro} from './readout.js';
import {trials,read} from './replay_api.js';
import {picker,state} from './trial_picker.js';
import {boards} from './clip_storyboard.js';
export async function render(outlet) {
 const rows=await trials();
 outlet.innerHTML=`${intro('脚本顺序','两个回放以同一组片段变更先后。试教分配固定一个版本，成绩与实际放映顺序关联。')}<div class="toolrow">${picker(rows)}</div><section class="split"><div class="scripts stack"></div><aside class="editor-note"><h2>编辑须知</h2><p>词组优先以 A 表示，情境优先以 B 表示。按水平重复抽取照常上课的匿名记录。</p></aside></section>`;
 const select=outlet.querySelector('select');
 async function draw(){
   if(!select.value)return;
   const record=rows.find(x=>x.code===select.value), clips=await read(record.code,'versions');
   outlet.querySelector('.scripts').innerHTML=`<p class="callout">${state[record.state]}</p>`+boards(clips);
 }
 select.onchange=draw;await draw();
}
