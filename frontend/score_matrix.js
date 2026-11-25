import {table} from './readout.js';
import {levels} from './trial_picker.js';
export function matrix(rows) {
 const header=['匿名码','版本分配','成绩'];
 return Object.entries(levels).map(([key,title])=>table(title,header,rows.filter(r=>r.level===key).map(r=>[r.learner,r.arm,r.score??'待登记']))).join('');
}
