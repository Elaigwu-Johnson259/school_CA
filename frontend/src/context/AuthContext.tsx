import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchCurrentUser, login as loginRequest, logout as logoutRequest } from "@/api/auth";
import { clearStoredTokens, getStoredTokens, setStoredTokens } from "@/utils/tokenStorage";
import type { AuthenticatedUser } from "@/types/auth";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // On first load, if we already have a stored access token, try to
  // resolve who's logged in (e.g. after a page refresh).
  useEffect(() => {
    const tokens = getStoredTokens();
    if (!tokens?.accessToken) {
      setIsLoading(false);
      return;
    }
    fetchCurrentUser()
      .then(setUser)
      .catch(() => clearStoredTokens())
      .finally(() => setIsLoading(false));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await loginRequest(email, password);
    setStoredTokens({ accessToken: response.access_token, refreshToken: response.refresh_token });
    setUser(response.user);
  }, []);

  const logout = useCallback(async () => {
    const tokens = getStoredTokens();
    if (tokens?.refreshToken) {
      // Best-effort: even if the server call fails (e.g. already expired),
      // we still clear local state so the user is logged out on this device.
      await logoutRequest(tokens.refreshToken).catch(() => undefined);
    }
    clearStoredTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
