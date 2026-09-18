import { useCallback, useEffect, useRef, useState } from 'react';
import { errorMessage } from '../utils/format';
/** Request-key based resource with stale-response protection and an explicit retry. */
export function useAsync<T>(key: string, loader: () => Promise<T>, enabled = true) {
  const loaderRef = useRef(loader);
  loaderRef.current = loader;
  const [nonce, setNonce] = useState(0);
  const [state, setState] = useState<{
    data: T | undefined;
    loading: boolean;
    error: string | null;
  }>({ data: undefined, loading: enabled, error: null });
  useEffect(() => {
    let active = true;
    if (!enabled) {
      setState({ data: undefined, loading: false, error: null });
      return;
    }
    setState({ data: undefined, loading: true, error: null });
    loaderRef.current().then((data) => {
      if (active)
        setState({ data, loading: false, error: null });
    })
      .catch((error: unknown) => {
        if (active)
          setState({ data: undefined, loading: false, error: errorMessage(error) });
      });
    return () => { active = false; };
  }, [key, nonce, enabled]);
  const reload = useCallback(() => setNonce((value) => value + 1), []);
  return { ...state, reload };
}
