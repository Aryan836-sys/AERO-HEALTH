import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react';
import type { User, Session } from '../types/api';
import { api, setAccessToken } from '../services/api';
interface AuthState {
  user: User | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<AuthState | null>(null);
export function AuthProvider({ children }: {
  children: ReactNode;
}) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const apply = useCallback((session: Session | null) => { setUser(session?.user ?? null); setAccessToken(session?.accessToken ?? null); }, []);
  useEffect(() => {
    let active = true;
    api.refresh().then((session) => {
      if (active)
        apply(session);
    }).catch(() => {
      if (active)
        apply(null);
    }).finally(() => {
      if (active)
        setReady(true);
    });
    const expired = () => apply(null);
    window.addEventListener('aero:session-expired', expired);
    return () => { active = false; window.removeEventListener('aero:session-expired', expired); };
  }, [apply]);
  const login = useCallback(async (email: string, password: string) => apply(await api.login(email, password)), [apply]);
  const register = useCallback(async (name: string, email: string, password: string) => apply(await api.register(name, email, password)), [apply]);
  const logout = useCallback(async () => { await api.logout(); apply(null); }, [apply]);
  return <AuthContext.Provider value={{ user, ready, login, register, logout }}>{children}</AuthContext.Provider>;
}
export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (!context)
    throw new Error('useAuth requires AuthProvider');
  return context;
}
