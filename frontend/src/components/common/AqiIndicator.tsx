import { useTranslation } from 'react-i18next';
import { AQI_CATEGORIES, getAqiCategory } from '../../utils/aqi';
export default function AqiIndicator({ value, compact = false, number = false }: {
  value: number | null | undefined;
  compact?: boolean;
  number?: boolean;
}) {
  const { t } = useTranslation();
  const category = getAqiCategory(value);
  if (!category)
    return <span className="aqi-badge aqi-missing">
      <span aria-hidden="true">?</span>
      {t('noData')}
    </span>;
  return <span className={`aqi-badge ${compact ? 'aqi-compact' : ''}`} style={{ color: category.ink, background: category.background }}>
    <span className="aqi-symbol" aria-hidden="true">{category.symbol}</span>
    {number && <strong>{Math.round(value!)}</strong>}
    {t(`aqi.${category.key}${compact ? '.short' : ''}`)}
  </span>;
}
export function AqiLegend({ detailed = false }: {
  detailed?: boolean;
}) {
  const { t } = useTranslation();
  return <div className={`aqi-legend ${detailed ? 'legend-detailed' : ''}`} aria-label={t('aqiScale')}>{AQI_CATEGORIES.map((category) => <div key={category.key}>
    <span className="legend-symbol" style={{ background: category.background, color: category.ink }}>{category.symbol}</span>
    <span>{t(`aqi.${category.key}.short`)}{detailed && <small>{category.min}{Number.isFinite(category.max) ? `–${category.max}` : '+'}</small>}</span>
  </div>)}</div>;
}
