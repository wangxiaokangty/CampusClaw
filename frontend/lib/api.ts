/**
 * 带 JWT 的 API 客户端。
 *
 * 所有请求/响应类型都从 `types/api.d.ts`（由后端 OpenAPI 生成）推导，
 * 本文件不声明任何接口形状——契约的唯一真相在后端（design.md D1）。
 */

import type { paths } from "@/types/api";

const JSON_MEDIA = "application/json";

/** 取某个操作的成功响应体类型（200 / 201，204 为 void）。 */
type SuccessBody<O> = O extends { responses: infer R }
  ? R extends { 200: { content: { [K in typeof JSON_MEDIA]: infer B } } }
    ? B
    : R extends { 201: { content: { [K in typeof JSON_MEDIA]: infer B } } }
      ? B
      : void
  : never;

type RequestBody<O> = O extends { requestBody?: { content: { [K in typeof JSON_MEDIA]: infer B } } }
  ? B
  : never;

type QueryOf<O> = O extends { parameters: { query?: infer Q } } ? Q : never;
type PathOf<O> = O extends { parameters: { path: infer P } } ? P : never;

type OpsOf<M extends string> = {
  [P in keyof paths]: paths[P] extends { [K in M]: infer O }
    ? O extends undefined
      ? never
      : P
    : never;
}[keyof paths];

export type GetPaths = OpsOf<"get">;
export type PostPaths = OpsOf<"post">;
export type PatchPaths = OpsOf<"patch">;
export type DeletePaths = OpsOf<"delete">;

/** 从某端点的成功响应中取类型，供组件标注 props。 */
export type Res<P extends GetPaths> = SuccessBody<paths[P]["get"]>;
export type PostRes<P extends PostPaths> = SuccessBody<paths[P]["post"]>;

// ---------------------------------------------------------------- 传输层

const TOKEN_KEY = "campusclaw.token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

/** 开发态直连后端，生产态走 Next.js rewrites 反代的同源 /api（design.md D10）。 */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string,
  ) {
    super(detail);
  }
}

function buildUrl(
  template: string,
  pathParams?: Record<string, string | number>,
  query?: Record<string, unknown>,
): string {
  let p = template;
  for (const [k, v] of Object.entries(pathParams ?? {})) {
    p = p.replace(`{${k}}`, encodeURIComponent(String(v)));
  }
  const search = new URLSearchParams();
  for (const [k, v] of Object.entries(query ?? {})) {
    if (v !== undefined && v !== null && v !== "") search.set(k, String(v));
  }
  const qs = search.toString();
  return `${API_BASE}${p}${qs ? `?${qs}` : ""}`;
}

export function authHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return headers;
}

async function request<T>(method: string, url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    method,
    headers: authHeaders(init?.headers),
  });
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  const body: unknown = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const detail =
      body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `请求失败（${res.status}）`;
    throw new ApiError(res.status, detail);
  }
  return body as T;
}

// ---------------------------------------------------------------- 各动词

type Opts<O> = (PathOf<O> extends never ? { path?: undefined } : { path: PathOf<O> }) &
  (QueryOf<O> extends never ? { query?: undefined } : { query?: QueryOf<O> });

export function apiGet<P extends GetPaths>(
  endpoint: P,
  ...[opts]: Opts<paths[P]["get"]> extends { path: unknown }
    ? [Opts<paths[P]["get"]>]
    : [Opts<paths[P]["get"]>?]
): Promise<SuccessBody<paths[P]["get"]>> {
  const o = (opts ?? {}) as { path?: Record<string, string>; query?: Record<string, unknown> };
  return request("GET", buildUrl(endpoint as string, o.path, o.query));
}

type ReqOpts<O> = { path?: PathOf<O>; query?: QueryOf<O> };

/** 无请求体的端点（如 POST .../explain）不必传 body。 */
type BodyArgs<O> = [RequestBody<O>] extends [never]
  ? [body?: undefined, opts?: ReqOpts<O>]
  : [body: RequestBody<O>, opts?: ReqOpts<O>];

function sendJson<T>(
  method: string,
  endpoint: string,
  body: unknown,
  opts: { path?: Record<string, string>; query?: Record<string, unknown> } | undefined,
): Promise<T> {
  return request(method, buildUrl(endpoint, opts?.path, opts?.query), {
    headers: { "Content-Type": JSON_MEDIA },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

export function apiPost<P extends PostPaths>(
  endpoint: P,
  ...args: BodyArgs<paths[P]["post"]>
): Promise<SuccessBody<paths[P]["post"]>> {
  const [body, opts] = args;
  return sendJson(
    "POST",
    endpoint as string,
    body,
    opts as { path?: Record<string, string>; query?: Record<string, unknown> } | undefined,
  );
}

export function apiPatch<P extends PatchPaths>(
  endpoint: P,
  ...args: BodyArgs<paths[P]["patch"]>
): Promise<SuccessBody<paths[P]["patch"]>> {
  const [body, opts] = args;
  return sendJson(
    "PATCH",
    endpoint as string,
    body,
    opts as { path?: Record<string, string>; query?: Record<string, unknown> } | undefined,
  );
}

export function apiDelete<P extends DeletePaths>(
  endpoint: P,
  opts?: ReqOpts<paths[P]["delete"]>,
): Promise<SuccessBody<paths[P]["delete"]>> {
  const o = (opts ?? {}) as { path?: Record<string, string>; query?: Record<string, unknown> };
  return request("DELETE", buildUrl(endpoint as string, o.path, o.query));
}

/** multipart 上传（讲义、技能包）。body 由调用方构造为 FormData。 */
export function apiUpload<P extends PostPaths>(
  endpoint: P,
  form: FormData,
  opts?: { path?: PathOf<paths[P]["post"]> },
): Promise<SuccessBody<paths[P]["post"]>> {
  const o = (opts ?? {}) as { path?: Record<string, string> };
  return request("POST", buildUrl(endpoint as string, o.path), { body: form });
}
