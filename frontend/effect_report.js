import {stats,table} from './readout.js';
import {levels,state} from './trial_picker.js';
export function report(data) {
 const r=data.effect;
 return stats([['轮次状态',state[data.state]],['B 相对 A（分）',r?.effect??'—'],['精确双侧 p',r?.p_value??'—'],['可交换分配',r?.permutations??'—']])+
 table('水平班结果',['分层','版本 A 人数','版本 B 人数','分数差'],(r?.detail??[]).map(x=>[levels[x.level],x.a,x.b,x.effect]));
}
