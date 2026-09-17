import type { Area } from '../types/api';
export const VALLEY_CENTER: [
  number,
  number
] = [27.701, 85.354];
export const VALLEY_BOUNDS: [
  [
    number,
    number
  ],
  [
    number,
    number
  ]
] = [[27.56, 85.19], [27.83, 85.53]];
export function distanceKm(a: Pick<Area, 'latitude' | 'longitude'>, b: Pick<Area, 'latitude' | 'longitude'>): number {
  const rad = (value: number) => (value * Math.PI) / 180;
  const dLat = rad(b.latitude - a.latitude);
  const dLng = rad(b.longitude - a.longitude);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a.latitude)) * Math.cos(rad(b.latitude)) * Math.sin(dLng / 2) ** 2;
  return 6371 * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(Math.max(0, 1 - h)));
}
export function nearestStation(area: Pick<Area, 'latitude' | 'longitude'>, areas: Area[]): {
  area: Area;
  distance: number;
} | null {
  const available = areas.filter((candidate) => candidate.reading !== null);
  if (!available.length)
    return null;
  const sorted = available.map((candidate) => ({ area: candidate, distance: distanceKm(area, candidate) })).sort((a, b) => a.distance - b.distance);
  return sorted[0];
}
export function isInValley(latitude: number, longitude: number): boolean {
  return latitude >= VALLEY_BOUNDS[0][0] && latitude <= VALLEY_BOUNDS[1][0] && longitude >= VALLEY_BOUNDS[0][1] && longitude <= VALLEY_BOUNDS[1][1];
}
