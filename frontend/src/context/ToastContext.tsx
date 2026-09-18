import { createContext, useCallback, useContext, useMemo, useEffect, useRef, useState, type ReactNode } from 'react';
import Icon from '../components/common/Icon';
interface Toast {
  id: number;
  text: string;
  type: 'success' | 'error' | 'info';
}
type Notify = (text: string, type?: Toast['type']) => void;
interface ToastApi extends Notify {
  success: (text: string) => void;
  error: (text: string) => void;
  info: (text: string) => void;
}
const ToastContext = createContext<ToastApi | null>(null);
export function ToastProvider({ children }: {
  children: ReactNode;
}) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  useEffect(() => () => timers.current.forEach(clearTimeout), []);
  const notify = useCallback((text: string, type: Toast['type'] = 'success') => {
    const id = Date.now() + Math.random();
    setToasts((items) => [...items.slice(-2), { id, text, type }]);
    timers.current.push(setTimeout(() => setToasts((items) => items.filter((item) => item.id !== id)), 5500));
  }, []);
  const value = useMemo(() => Object.assign(notify, { success: (text: string) => notify(text, 'success'), error: (text: string) => notify(text, 'error'), info: (text: string) => notify(text, 'info') }), [notify]);
  return <ToastContext.Provider value={value}>
    {children}
    <div className="toast-stack" aria-live="polite" aria-atomic="false">{toasts.map((toast) => <div key={toast.id} className={`toast toast-${toast.type}`} role={toast.type === 'error' ? 'alert' : 'status'}>
      <Icon name={toast.type === 'error' ? 'alert' : toast.type === 'success' ? 'check-circle' : 'info'} />
      <span>{toast.text}</span>
      <button type="button" aria-label="Dismiss message" className="icon-button" onClick={() => setToasts((items) => items.filter((item) => item.id !== toast.id))}>
        <Icon name="close" size={16} />
      </button>
    </div>)}</div>
  </ToastContext.Provider>;
}
export function useToast() {
  const context = useContext(ToastContext);
  if (!context)
    throw new Error('useToast requires ToastProvider');
  return context;
}
