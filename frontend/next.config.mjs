/** @type {import('next').NextConfig} */
const nextConfig = {
  // 生产态：由 Next.js 反代 /api 到后端服务，浏览器侧无跨域（design.md D10）。
  // rewrites 在构建时固化进路由清单，所以 API_PROXY_TARGET 是构建期参数。
  output: "standalone",
  async rewrites() {
    const target = process.env.API_PROXY_TARGET;
    if (!target) return [];
    return [{ source: "/api/:path*", destination: `${target}/api/:path*` }];
  },
};

export default nextConfig;
