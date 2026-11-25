import {waitJob} from './base.js';
import {intro} from './readout.js';
import {feedback,onSubmit} from './submit.js';
import {trials,read,write} from './replay_api.js';
import {picker} from './trial_picker.js';
import {report} from './effect_report.js';
export async function render(outlet,user) {
 const rows=await trials();
 outlet.innerHTML=`${intro('置换复核','在每个水平班内交换实际版本标签，保持人数，计算出现同等或更大分差的次数。')}<form class="toolrow">${picker(rows)}${user.role==='reviewer'?'<button>冻结并计算对照</button>':''}${feedback}</form><div class="effect band"></div>`;
 const select=outlet.querySelector('select');
 async function draw(){if(select.value)outlet.querySelector('.effect').innerHTML=report(await read(select.value,'effect'));}
 select.onchange=draw;
 onSubmit(outlet.querySelector('form'),async()=>{const job=await write(select.value,'effect');await waitJob(job.job_id);await draw();return '置换复核已完成';});
 await draw();
}
