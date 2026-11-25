import {h} from './base.js';
export const boards=versions=>versions.map(v=>`<article><h2>回放 ${h(v.arm)}</h2><div class="replay-strip">${v.clips.map(x=>`<span>${h(x)}</span>`).join('')}</div></article>`).join('');
