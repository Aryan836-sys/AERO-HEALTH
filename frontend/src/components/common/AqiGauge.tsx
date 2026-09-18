import { useId } from 'react';
import { useTranslation } from 'react-i18next';
import { AQI_CATEGORIES, clamp, getAqiCategory } from '../../utils/aqi';
import AqiIndicator from './AqiIndicator';
function point(value: number): [
  number,
  number
] { const angle = Math.PI + (clamp(value, 0, 500) / 500) * Math.PI; return [140 + 107 * Math.cos(angle), 125 + 107 * Math.sin(angle)]; }
export default function AqiGauge({ value }: {
  value: number | null;
}) {
  const { t } = useTranslation();
  const id = useId();
  const category = getAqiCategory(value);
  const [x, y] = point(value ?? 0);
  return <div className="aqi-gauge">
    <svg viewBox="0 0 280 155" role="img" aria-labelledby={id}>
      <title id={id}>{value === null ? t('noDirectData') : `US AQI ${value}: ${t(`aqi.${category?.key}`)}`}</title>
      {AQI_CATEGORIES.map((item) => { const [sx, sy] = point(item.min === 0 ? 0 : item.min + 1); const [ex, ey] = point(Math.min(item.max, 500) - 2); return <path key={item.key} d={`M${sx} ${sy} A107 107 0 0 1 ${ex} ${ey}`} fill="none" stroke={value === null ? '#e0e6e3' : item.color} strokeWidth="9" strokeLinecap="round" />; })}
      {category && <>
        <circle cx={x} cy={y} r="9" fill="white" stroke={category.color} strokeWidth="4" />
        <circle cx={x} cy={y} r="2" fill={category.color} />
      </>}
      <text x="140" y="105" textAnchor="middle" className="gauge-number">{value ?? '\u2014'}</text>
      <text x="140" y="126" textAnchor="middle" className="gauge-caption">US AQI</text>
      <text x="30" y="150" className="gauge-tick">0</text>
      <text x="239" y="150" className="gauge-tick">500</text>
    </svg>
    <AqiIndicator value={value} />
  </div>;
}
