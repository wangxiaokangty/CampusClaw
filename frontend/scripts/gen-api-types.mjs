#!/usr/bin/env node
/**
 * 从后端 FastAPI 导出的 OpenAPI 生成 `types/api.d.ts`（design.md D1）。
 *
 * 契约的唯一真相是后端代码，前端不手写任何接口类型。
 *
 * 用法：
 *   node scripts/gen-api-types.mjs          # 生成并写入 types/api.d.ts
 *   node scripts/gen-api-types.mjs --check  # 只校验：生成物与提交物不一致则退出码 1
 */

import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import openapiTS, { astToString } from "openapi-typescript";

const HERE = dirname(fileURLToPath(import.meta.url));
const FRONTEND = resolve(HERE, "..");
const BACKEND = resolve(FRONTEND, "..", "backend");
const OUT = join(FRONTEND, "types", "api.d.ts");

const check = process.argv.includes("--check");

/** 调用后端导出 OpenAPI —— 不复制一份 schema，直接问真相本身。 */
function exportOpenApi() {
  const tmp = mkdtempSync(join(tmpdir(), "campusclaw-openapi-"));
  const specPath = join(tmp, "openapi.json");
  try {
    execFileSync("uv", ["run", "python", "scripts/export_openapi.py", specPath], {
      cwd: BACKEND,
      stdio: ["ignore", "ignore", "inherit"],
    });
    return readFileSync(specPath, "utf8");
  } finally {
    rmSync(tmp, { recursive: true, force: true });
  }
}

const spec = JSON.parse(exportOpenApi());
const ast = await openapiTS(spec, { alphabetize: true });
const generated =
  "/**\n * 由 `npm run gen:api` 从后端 OpenAPI 自动生成 —— 请勿手工编辑。\n */\n\n" +
  astToString(ast);

if (check) {
  const current = existsSync(OUT) ? readFileSync(OUT, "utf8") : "";
  if (current !== generated) {
    console.error(
      "[check:api] types/api.d.ts 与后端 OpenAPI 不一致。请运行 `npm run gen:api` 并提交生成物。"
    );
    process.exit(1);
  }
  console.log("[check:api] 契约一致。");
} else {
  writeFileSync(OUT, generated, "utf8");
  console.log(`[gen:api] 已生成 ${OUT}`);
}
