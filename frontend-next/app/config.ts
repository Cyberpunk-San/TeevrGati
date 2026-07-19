// API_URL is intentionally empty so all /api/* requests are routed through
// the Next.js rewrite proxy defined in next.config.mjs — this eliminates CORS
// in production. Override with NEXT_PUBLIC_API_URL for direct-backend mode.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
export const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "dev-key";
