import {stats,table} from './readout.js';
import {levels,state} from './trial_picker.js';
import {h} from './base.js';
export function report(data) {
 const r=data.effect;
 const basis=r
   ? `第 ${h(data.revision)} 轮结果，当前有效，可作为签批依据`
   : (data.state==='revising'
       ? `第 ${h(data.revision)} 轮更正待重新冻结，旧结果已失效，不能用于签批`
       : `第 ${h(data.revision)} 轮结果尚未生成`);
 return stats([['轮次状态',state[data.state]],['当前修订轮次','第 '+data.revision+' 轮'],['B 相对 A（分）',r?.effect??'—'],['精确双侧 p',r?.p_value??'—'],['可交换分配',r?.permutations??'—']])+
 `<p class="callout">签批依据：${h(basis)}</p>`+
 table('水平班结果',['分层','版本 A 人数','版本 B 人数','分数差'],(r?.detail??[]).map(x=>[levels[x.level],x.a,x.b,x.effect]));
}
