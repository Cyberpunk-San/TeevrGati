/** @type {import('next').NextConfig} */
const nextConfig = {
  // Security headers applied to every Next.js response
  async headers() {
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "";
    const connectSrc = ["'self'", "http://localhost:8000", "https://localhost:8000"];
    if (backendUrl && !connectSrc.includes(backendUrl)) {
      connectSrc.push(backendUrl);
    }

    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options",  value: "nosniff" },
          { key: "X-Frame-Options",          value: "DENY" },
          { key: "X-XSS-Protection",         value: "1; mode=block" },
          { key: "Referrer-Policy",           value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy",        value: "geolocation=(), microphone=(), camera=()" },
          {
            key: "Content-Security-Policy",
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' 'unsafe-eval'", // Next.js requires these
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob:",
              `connect-src ${connectSrc.join(" ")}`,  // API backend
              "frame-ancestors 'none'",
            ].join("; "),
          },
        ],
      },
    ];
  },

  // Rewrites: proxy /api/* to the backend so the browser never makes
  // cross-origin requests in production (eliminates CORS entirely when deployed)
  async rewrites() {
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
