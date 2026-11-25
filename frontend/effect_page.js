import {waitJob} from './base.js';
import {intro} from './readout.js';
import {feedback,onSubmit} from './submit.js';
import {trials,read,write,refreeze} from './replay_api.js';
import {picker} from './trial_picker.js';
import {report} from './effect_report.js';
export async function render(outlet,user) {
 const rows=await trials();
 outlet.innerHTML=`${intro('置换复核','在每个水平班内交换实际版本标签，保持人数，计算出现同等或更大分差的次数。更正受理后须重新冻结，旧结果不再作为签批依据。')}<form class="toolrow">${picker(rows)}<span class="actions"></span>${feedback}</form><div class="effect band"></div>`;
 const select=outlet.querySelector('select');
 const actions=outlet.querySelector('.actions');
 async function draw(){
   if(!select.value)return;
   const record=rows.find(r=>r.code===select.value);
   actions.innerHTML=user.role==='reviewer'
     ? (record.state==='open' ? '<button>冻结并计算对照</button>'
        : record.state==='revising' ? '<button>按更正后成绩重新冻结并计算</button>' : '')
     : '';
   outlet.querySelector('.effect').innerHTML=report(await read(select.value,'effect'));
 }
 select.onchange=draw;
 onSubmit(outlet.querySelector('form'),async()=>{
   const record=rows.find(r=>r.code===select.value);
   const job=record.state==='revising' ? await refreeze(select.value) : await write(select.value,'effect');
   await waitJob(job.job_id);
   rows.splice(0,rows.length,...await trials());
   await draw();
   return record.state==='revising'?'已按更正后成绩重新冻结并出结果':'置换复核已完成';
 });
 await draw();
}
