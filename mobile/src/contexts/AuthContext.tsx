import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';

import { login as loginWithApi, type LoginPayload } from '@/services/api';
import { getStoredToken, removeStoredToken, saveToken } from '@/services/token-storage';

type AuthContextValue = {
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (credentials: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type AuthProviderProps = {
  children: ReactNode;
};

export function AuthProvider({ children }: AuthProviderProps) {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function restoreSession() {
      try {
        const storedToken = await getStoredToken();

        if (isMounted) {
          setToken(storedToken);
        }
      } catch (error) {
        console.warn('Impossible de restaurer la session.', error);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    void restoreSession();

    return () => {
      isMounted = false;
    };
  }, []);

  const login = useCallback(async (credentials: LoginPayload) => {
    const { access_token } = await loginWithApi(credentials);

    await saveToken(access_token);
    setToken(access_token);
  }, []);

  const logout = useCallback(async () => {
    try {
      await removeStoredToken();
    } finally {
      setToken(null);
    }
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      isAuthenticated: token !== null,
      loading,
      login,
      logout,
    }),
    [loading, login, logout, token]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth doit être utilisé à l’intérieur de AuthProvider.');
  }

  return context;
}
