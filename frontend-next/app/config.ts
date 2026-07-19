// API_URL is intentionally empty so all /api/* requests are routed through
// the Next.js rewrite proxy defined in next.config.mjs — this eliminates CORS
// in production. Override with NEXT_PUBLIC_API_URL for direct-backend mode.
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";
export const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "dev-key";

export const PLANT_NAME = process.env.NEXT_PUBLIC_PLANT_NAME || "BPCL Mathura Refinery";
export const ASSET_LIST = process.env.NEXT_PUBLIC_ASSET_LIST || "P-201, C-101, T-301";
export const DEFAULT_ASSET_ID = process.env.NEXT_PUBLIC_DEFAULT_ASSET_ID || "P-201";
export const DEFAULT_QUERY = process.env.NEXT_PUBLIC_DEFAULT_QUERY || "Pump P-201 is vibrating loudly. What could be wrong?";
