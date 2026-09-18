import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import type { Area, HealthProfile, AlertRule } from '../types/api';
import { api } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import { useAuth } from './AuthContext';
interface AppState {
  areas: Area[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
  selectedId: string;
  selectArea: (id: string) => void;
  favorites: string[];
  alerts: AlertRule[];
  profile: HealthProfile | null;
  userDataLoading: boolean;
  userDataError: string | null;
  refreshUser: () => void;
}
const AppContext = createContext<AppState | null>(null);
export function AppProvider({ children }: {
  children: ReactNode;
}) {
  const { user } = useAuth();
  const [selectedId, selectArea] = useState('ratnapark');
  const locations = useAsync('locations', api.getLocations);
  const userData = useAsync(`user:${user?.id ?? 'guest'}`, async () => {
    const [favorites, alerts, profile] = await Promise.all([api.getFavorites(), api.getAlerts(), api.getProfile()]);
    return { favorites, alerts, profile };
  }, !!user);
  useEffect(() => { const reload = () => userData.reload(); window.addEventListener('aero:data-changed', reload); return () => window.removeEventListener('aero:data-changed', reload); }, [userData.reload]);
  return <AppContext.Provider value={{ areas: locations.data ?? [], loading: locations.loading, error: locations.error, refresh: locations.reload, selectedId, selectArea, favorites: userData.data?.favorites ?? [], alerts: userData.data?.alerts ?? [], profile: userData.data?.profile ?? null, userDataLoading: userData.loading, userDataError: userData.error, refreshUser: userData.reload }}>{children}</AppContext.Provider>;
}
export function useApp(): AppState {
  const context = useContext(AppContext);
  if (!context)
    throw new Error('useApp requires AppProvider');
  return context;
}
