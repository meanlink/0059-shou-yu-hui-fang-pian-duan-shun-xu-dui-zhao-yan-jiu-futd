import {mount} from './base.js';
import {render as versions} from './versions_page.js';
import {render as scores} from './scores_page.js';
import {render as effect} from './effect_page.js';
import {render as memo} from './memo_page.js';
const pages = {"versions": "脚本顺序", "scores": "匿名试教", "effect": "置换复核", "memo": "教材签批"};
const screens = {versions, scores, effect, memo};
mount({title: "手语回放 · 片段顺序对照研究", kicker: "教材编辑 / 回放顺序", pages, render: (page, outlet, user) => screens[page](outlet, user)});
