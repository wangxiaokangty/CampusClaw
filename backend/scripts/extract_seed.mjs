#!/usr/bin/env node
/**
 * 从 CampusClaw 前端演示 bundle 中提取种子数据。
 *
 * 演示的种子数据不是字面量，而是由 bundle 内的构造函数生成的（多个学科配置
 * 交叉生成讲义、知识块、助手与作业）。因此这里的做法是把 bundle 中那段数据
 * 构造代码原样切出来执行，再导出结果——而不是人工转写，避免转写错误。
 *
 * 用法：
 *   node scripts/extract_seed.mjs [bundleUrlOrPath] [outPath]
 * 默认：
 *   bundle = https://devops.hello1023.com/demo-src/dist/assets/index-CSzGj5gY.js
 *   out    = app/seed/data.json
 */

import { writeFileSync, readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const DEFAULT_BUNDLE =
  "https://devops.hello1023.com/demo-src/dist/assets/index-CSzGj5gY.js";
const DEFAULT_OUT = resolve(HERE, "..", "app", "seed", "data.json");

// 数据构造代码在 bundle 中的起止锚点
const START = 'const Xm=[{id:"cls-a"';
const END = "auditLogs:mv}";

async function loadBundle(src) {
  if (existsSync(src)) return readFileSync(src, "utf8");
  const res = await fetch(src);
  if (!res.ok) throw new Error(`拉取 bundle 失败: ${res.status} ${src}`);
  return await res.text();
}

function sliceDataModule(bundle) {
  const a = bundle.indexOf(START);
  const b = bundle.indexOf(END);
  if (a < 0 || b < 0 || b <= a) {
    throw new Error(
      "未能在 bundle 中定位数据构造代码。上游演示可能已重新打包，" +
        "需要更新 START / END 锚点。",
    );
  }
  // 切片止于 vv 对象的末尾字段，补回闭合并导出内部标识符
  return (
    bundle.slice(a, b) +
    "auditLogs:mv};\n" +
    "export const seed = { classes: Xm, users: Jm, lectures: ov, kbChunks: uv," +
    " assistants: cv, homeworks: dv, submissions: fv, mistakes: pv, auditLogs: mv };\n"
  );
}

const [, , bundleArg, outArg] = process.argv;
const bundleSrc = bundleArg || DEFAULT_BUNDLE;
const outPath = outArg || DEFAULT_OUT;

const bundle = await loadBundle(bundleSrc);
const moduleSource = sliceDataModule(bundle);
const dataUrl =
  "data:text/javascript;base64," + Buffer.from(moduleSource).toString("base64");
const { seed } = await import(dataUrl);

// 稳定排序，保证脚本可重复执行且输出逐字节一致
const sortById = (xs) => [...xs].sort((x, y) => (x.id < y.id ? -1 : x.id > y.id ? 1 : 0));
const out = Object.fromEntries(
  Object.entries(seed).map(([k, v]) => [k, sortById(v)]),
);

const counts = Object.fromEntries(
  Object.entries(out).map(([k, v]) => [k, v.length]),
);
writeFileSync(outPath, JSON.stringify(out, null, 2) + "\n", "utf8");
console.log("来源:", bundleSrc);
console.log("写入:", outPath);
console.table(counts);
