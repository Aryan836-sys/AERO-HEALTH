import { useId, useMemo, useState } from 'react';
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { useTranslation } from 'react-i18next';
import type { Range, TrendPoint } from '../../types/api';
import { api, IS_DEMO } from '../../services/api';
import { demoForecast } from '../../services/fixtures';
import { useAsync } from '../../hooks/useAsync';
import { useReducedMotion } from '../../hooks/useReducedMotion';
import { downloadCsv, formatDate, formatTime } from '../../utils/format';
import Icon from '../common/Icon';
import { EmptyState, ErrorState, LoadingState } from '../common/states';
interface Props {
  areaId: string;
  areaName: string;
  compareId?: string;
  compareName?: string;
  compact?: boolean;
  initialRange?: Range;
}
export default function TrendChart({ areaId, areaName, compareId, compareName, compact = false, initialRange = '24h' }: Props) {
  const { t, i18n } = useTranslation();
  const reducedMotion = useReducedMotion();
  const rawId = useId();
  const id = rawId.replace(/[^a-zA-Z0-9]/g, '');
  const [range, setRange] = useState<Range>(initialRange);
  const [table, setTable] = useState(false);
  const [forecast, setForecast] = useState(false);
  const result = useAsync(`trend:${areaId}:${compareId ?? ''}:${range}:${forecast}`, async () => {
    if (forecast && IS_DEMO && !compareId)
      return { first: demoForecast(areaId), second: [] as TrendPoint[] };
    const [first, second] = await Promise.all([api.getTrend(areaId, range), compareId ? api.getTrend(compareId, range) : Promise.resolve([] as TrendPoint[])]);
    return { first, second };
  });
  const data = useMemo(() => {
    const other = new Map(result.data?.second.map((point) => [point.time, point.aqi]) ?? []);
    return (result.data?.first ?? []).map((point) => ({ ...point, comparison: other.get(point.time) ?? null }));
  }, [result.data]);
  const values = data.map((point) => forecast ? point.forecast : point.aqi).filter((value): value is number => typeof value === 'number');
  const summary = values.length ? { min: Math.min(...values), max: Math.max(...values), avg: Math.round(values.reduce((a, b) => a + b, 0) / values.length) } : null;
  const exportData = () => downloadCsv(`aero-health-${areaId}-${range}${forecast ? '-projection' : ''}.csv`, [['Dataset', IS_DEMO ? 'FICTIONAL DEMO DATA' : 'Configured backend'], ['Timestamp (UTC)', `${areaName} US AQI`, ...(compareId ? [`${compareName} US AQI`] : [])], ...data.map((point) => [point.time, (forecast ? point.forecast : point.aqi) ?? null, ...(compareId ? [point.comparison] : [])])]);
  return <section className={`trend-panel ${compact ? 'trend-compact' : ''}`}>
    <div className="section-heading">
      <div>
        <p className="eyebrow">{forecast ? t('forecast') : t('historical')}</p>
        <h2>{t('airTrend')}</h2>
        <p className="muted small">{areaName}{compareName ? ` / ${compareName}` : ` \u00b7 ${t('trendDescription')}`}</p>
      </div>
      <button className="icon-button" title={t('exportCsv')} aria-label={t('exportCsv')} onClick={exportData} disabled={!data.length}>
        <Icon name="download" size={18} />
      </button>
    </div>
    <div className="chart-toolbar">{!forecast && <div className="segmented" aria-label="Time range">{(['24h', '7d', '30d'] as Range[]).map((item) => <button key={item} onClick={() => setRange(item)} aria-pressed={range === item} className={range === item ? 'active' : ''}>{t(`range.${item}`)}</button>)}</div>}{IS_DEMO && !compareId && <button className={`text-button ${forecast ? 'text-violet' : ''}`} onClick={() => setForecast(!forecast)} aria-pressed={forecast}>
      <Icon name="sparkles" size={14} />
      {t(forecast ? 'historical' : 'forecast')}
    </button>}</div>
    {result.loading ? <LoadingState compact /> : result.error ? <ErrorState message={result.error} onRetry={result.reload} /> : !data.length ? <EmptyState title={t('noTrend')} /> : <>
      {table ? <div className="data-table-scroll chart-data">
        <table>
          <caption className="sr-only">{t('chartAria', { area: areaName })}</caption>
          <thead>
            <tr>
              <th>{t('observationTime')} (NPT)</th>
              <th>{areaName} / AQI</th>
              {compareId && <th>{compareName} / AQI</th>}
            </tr>
          </thead>
          <tbody>{data.map((point) => <tr key={point.time}>
            <td>{formatDate(point.time, i18n.language)} {formatTime(point.time, i18n.language)}</td>
            <td>{(forecast ? point.forecast : point.aqi) ?? t('missing')}</td>
            {compareId && <td>{point.comparison ?? t('missing')}</td>}
          </tr>)}</tbody>
        </table>
      </div> : <div className="chart-canvas" role="img" aria-label={t('chartAria', { area: areaName })}>
        <ResponsiveContainer width="100%" height={compact ? 180 : 220} minWidth={0}>
          <AreaChart data={data} margin={{ top: 16, right: 10, left: -26, bottom: 0 }} accessibilityLayer>
            <defs>
              <linearGradient id={`mint-${id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#18b78e" stopOpacity={0.2} />
                <stop offset="100%" stopColor="#18b78e" stopOpacity={0.015} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="#edf0ed" strokeDasharray="3 5" />
            <XAxis dataKey="time" axisLine={false} tickLine={false} minTickGap={30} tick={{ fill: '#71807a', fontSize: 10 }} tickFormatter={(value: string) => range === '24h' || forecast ? formatTime(value, i18n.language) : formatDate(value, i18n.language)} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#71807a', fontSize: 10 }} domain={[0, 'auto']} tickCount={4} />
            <Tooltip contentStyle={{ border: '1px solid #e1e8e3', borderRadius: '14px', boxShadow: '0 8px 28px #18312e12', fontSize: 12 }} labelFormatter={(label) => `${formatDate(String(label), i18n.language)} ${formatTime(String(label), i18n.language)} NPT`} formatter={(value, name) => [`${value ?? t('missing')} AQI`, name ?? areaName]} />
            <Area type="monotone" dataKey={forecast ? 'forecast' : 'aqi'} name={areaName} stroke="#10ac84" strokeWidth={2.6} fill={`url(#mint-${id})`} dot={false} activeDot={{ r: 5, stroke: 'white', strokeWidth: 3 }} strokeDasharray={forecast ? '6 5' : undefined} connectNulls={false} isAnimationActive={!reducedMotion} animationDuration={650} />
            {compareId && <Area type="monotone" dataKey="comparison" name={compareName} stroke="#7962d6" strokeWidth={2.2} strokeDasharray="5 4" fill="transparent" dot={false} connectNulls={false} isAnimationActive={!reducedMotion} />}
          </AreaChart>
        </ResponsiveContainer>
      </div>}
      {compareId && <div className="chart-legend">
        <span>
          <i />
          {areaName}
        </span>
        <span>
          <i className="dashed" />
          {compareName}
        </span>
      </div>}
      {summary && !compact && <div className="chart-stats">
        <div>
          <span>{t('minimum')}</span>
          <strong>
            {summary.min}
            <small> AQI</small>
          </strong>
        </div>
        <div>
          <span>{t('average')}</span>
          <strong>
            {summary.avg}
            <small> AQI</small>
          </strong>
        </div>
        <div>
          <span>{t('maximum')}</span>
          <strong>
            {summary.max}
            <small> AQI</small>
          </strong>
        </div>
      </div>}
    </>}
    <div className="chart-foot">
      <p>
        <Icon name="info" size={12} />
        {IS_DEMO ? t(forecast ? 'forecastNote' : 'trendNote') : t('timeZone')}
      </p>
      <button className="text-button" onClick={() => setTable(!table)} aria-pressed={table}>{t(table ? 'showChart' : 'showTable')}</button>
    </div>
  </section>;
}
