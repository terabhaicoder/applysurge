import { AuthTokens } from "@/types/api";

const ACCESS_TOKEN_KEY = "applysurge_access_token";
const REFRESH_TOKEN_KEY = "applysurge_refresh_token";
const TOKEN_EXPIRY_KEY = "applysurge_token_expiry";

export function getTokens(): AuthTokens | null {
  if (typeof window === "undefined") return null;

  const access_token = localStorage.getItem(ACCESS_TOKEN_KEY);
  const refresh_token = localStorage.getItem(REFRESH_TOKEN_KEY);

  if (!access_token || !refresh_token) return null;

  return {
    access_token,
    refresh_token,
    token_type: "bearer",
    expires_in: getTokenExpiry(),
  };
}

export function setTokens(tokens: AuthTokens): void {
  if (typeof window === "undefined") return;

  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);

  const expiryTime = Date.now() + tokens.expires_in * 1000;
  localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(TOKEN_EXPIRY_KEY);
}

export function getTokenExpiry(): number {
  if (typeof window === "undefined") return 0;

  const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY);
  if (!expiry) return 0;

  const remaining = (parseInt(expiry) - Date.now()) / 1000;
  return Math.max(0, Math.floor(remaining));
}

export function isTokenExpired(): boolean {
  const expiry = getTokenExpiry();
  return expiry <= 0;
}

export function shouldRefreshToken(): boolean {
  const expiry = getTokenExpiry();
  return expiry > 0 && expiry < 300; // Refresh if less than 5 minutes left
}
