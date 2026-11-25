import {api} from './base.js';
const path='/api/sign-trials';
export const trials=()=>api(path);
export const read=(code,section)=>api(`${path}/${encodeURIComponent(code)}/${section}`);
export const write=(code,section,body)=>api(`${path}/${encodeURIComponent(code)}/${section}`,section==='scores'?'PUT':'POST',body);
export const correct=(code,body)=>api(`${path}/${encodeURIComponent(code)}/corrections`,'POST',body);
export const refreeze=code=>api(`${path}/${encodeURIComponent(code)}/refreeze`,'POST');
