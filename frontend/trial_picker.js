import {options} from './submit.js';
export const picker=rows=>`<label>手语试教<select name="trial">${options(rows.map(r=>[r.code,r.code+' · '+r.lesson]))}</select></label>`;
export const state={open:'可登记',frozen:'已冻结，后台计算',evaluated:'待教材签批',signed:'已签批',revising:'更正中，待重新冻结'};
export const levels={beginner:'初学',returning:'续学'};
