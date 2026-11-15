#!/usr/bin/env node
/* 校验 data/specs.js 的键是否能在 data/dashboard.js 里找到对应品牌与车型。
 * 参数层靠「品牌名|车型名」精确匹配前端模型行，键写错/车型不在库里 = 数据永不显示。
 * 用法：node tools/check_specs.js  （退出码 1 表示有不匹配）
 */
const path = require("path");
const globals = {};
global.window = globals;

const dir = path.join(__dirname, "..", "data");
require(path.join(dir, "dashboard.js"));
const D = globals.MOTO_DATA;
globals.MOTO_SPECS = undefined;
require(path.join(dir, "specs.js"));
const S = (globals.MOTO_SPECS && globals.MOTO_SPECS.models) || {};

const keys = Object.keys(S);
const bad = [];
keys.forEach(function (k) {
  const parts = k.split("|");
  if (parts.length !== 2) { bad.push(k + " （键格式错误，应为 品牌名|车型名）"); return; }
  const b = D.brands.filter(function (x) { return x.name === parts[0]; })[0];
  if (!b) { bad.push(k + " （库里没有该品牌）"); return; }
  if (!b.models.some(function (m) { return m.name === parts[1]; })) bad.push(k + " （该品牌下没有这个车型名）");
});

const total = (globals.MOTO_SPECS.meta && globals.MOTO_SPECS.meta.totalModels) || 0;
console.log("参数条目 " + keys.length + " ｜ 库内车型 " + total + " ｜ 不匹配 " + bad.length);
if (bad.length) {
  console.error(bad.join("\n"));
  process.exit(1);
}
