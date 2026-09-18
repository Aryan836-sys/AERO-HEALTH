import type { CategoryKey } from '../types/api';
export interface AqiCategory {
  key: CategoryKey;
  min: number;
  max: number;
  color: string;
  ink: string;
  background: string;
  symbol: string;
}
// US AQI category thresholds; colors are visual tokens, not the only status cue.
// Source: https://www.airnow.gov/aqi/aqi-basics/
export const AQI_CATEGORIES: readonly AqiCategory[] = [
  { key: 'good', min: 0, max: 50, color: '#16b68c', ink: '#086c51', background: '#e6f7f0', symbol: '\u2713' },
  { key: 'moderate', min: 51, max: 100, color: '#e9b62f', ink: '#78570a', background: '#fff5d7', symbol: '~' },
  { key: 'sensitive', min: 101, max: 150, color: '#ed8a45', ink: '#9b3e12', background: '#fff0e3', symbol: '!' },
  { key: 'unhealthy', min: 151, max: 200, color: '#e65a64', ink: '#a4273c', background: '#ffebee', symbol: '!!' },
  { key: 'veryUnhealthy', min: 201, max: 300, color: '#9363cd', ink: '#63329a', background: '#f1eafb', symbol: '!!!' },
  { key: 'hazardous', min: 301, max: Infinity, color: '#8e355b', ink: '#7b244a', background: '#f9e8ef', symbol: '\u00d7' },
];
export function getAqiCategory(aqi: number | null | undefined): AqiCategory | null {
  if (aqi === null || aqi === undefined || !Number.isFinite(aqi) || aqi < 0)
    return null;
  // Category boundaries are based on the displayed integer AQI.
  const value = Math.round(aqi);
  return AQI_CATEGORIES.find((category) => value <= category.max) ?? null;
}
export function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}
