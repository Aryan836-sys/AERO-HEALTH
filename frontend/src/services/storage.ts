const PREFIX = 'aero-health-v2:';
export function readStored<T>(key: string, fallback: T, temporary = false): T {
  try {
    const raw = (temporary ? sessionStorage : localStorage).getItem(PREFIX + key);
    return raw ? JSON.parse(raw) as T : fallback;
  }
  catch {
    return fallback;
  }
}
export function writeStored<T>(key: string, value: T, temporary = false): void {
  try {
    (temporary ? sessionStorage : localStorage).setItem(PREFIX + key, JSON.stringify(value));
  }
  catch {
    throw new Error('Browser storage is unavailable or full. Remove a large demo photo or allow site storage, then retry.');
  }
}
export function removeStored(key: string, temporary = false): void {
  (temporary ? sessionStorage : localStorage).removeItem(PREFIX + key);
}
export function notifyDataChanged(): void { window.dispatchEvent(new Event('aero:data-changed')); }
