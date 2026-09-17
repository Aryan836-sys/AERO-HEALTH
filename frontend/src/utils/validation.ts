export const MAX_PHOTO_BYTES = 5 * 1024 * 1024;
export function validatePhoto(file: Pick<File, 'size' | 'type'>): string | null {
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type))
    return 'photoType';
  if (file.size > MAX_PHOTO_BYTES)
    return 'photoSize';
  if (file.size === 0)
    return 'photoEmpty';
  return null;
}
export function validEmail(value: string): boolean { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value); }
export function validThreshold(value: number): boolean { return Number.isInteger(value) && value >= 1 && value <= 500; }
