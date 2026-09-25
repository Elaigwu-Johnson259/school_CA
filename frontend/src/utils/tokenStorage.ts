/**
 * Tokens live in localStorage so a page refresh doesn't log the user out.
 *
 * Trade-off worth knowing as a beginner: localStorage is readable by any
 * JS running on the page, so it's vulnerable to XSS (unlike an httpOnly
 * cookie, which JS can't read at all). That's an acceptable starting
 * point for Phase 3 — moving refresh tokens to an httpOnly cookie is a
 * reasonable hardening step for a later phase, not something Phase 3
 * needs to solve.
 */
const STORAGE_KEY = "school_results_auth_tokens";

export interface StoredTokens {
  accessToken: string;
  refreshToken: string;
}

export function getStoredTokens(): StoredTokens | null {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StoredTokens;
  } catch {
    return null;
  }
}

export function setStoredTokens(tokens: StoredTokens): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens));
}

export function clearStoredTokens(): void {
  localStorage.removeItem(STORAGE_KEY);
}
