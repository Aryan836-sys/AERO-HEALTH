import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { District, Pollutant, Reliability } from '../../types/api';
import Icon from '../common/Icon';
export interface Filters {
  query: string;
  district: 'All' | District;
  source: 'all' | Reliability;
  metric: 'AQI' | Pollutant;
  allStations: boolean;
}
export const DEFAULT_FILTERS: Filters = { query: '', district: 'All', source: 'all', metric: 'AQI', allStations: false };
export default function MapFilters({ filters, onChange, floating = false }: {
  filters: Filters;
  onChange: (value: Filters) => void;
  floating?: boolean;
}) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(!floating || window.innerWidth > 800);
  const set = <K extends keyof Filters>(key: K, value: Filters[K]) => onChange({ ...filters, [key]: value });
  return <div className={`map-filters ${floating ? 'floating-filters' : ''} ${expanded ? 'filters-expanded' : ''}`}>
    <button className="filter-title" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>
      <span>
        <Icon name="filter" size={18} />
        {t('airQualityView')}
      </span>
      <Icon name="chevron-down" size={15} />
    </button>
    <div className="filter-content">
      <label className="search-input">
        <Icon name="search" size={16} />
        <input aria-label={t('searchArea')} value={filters.query} onChange={(event) => set('query', event.target.value)} placeholder={t('searchArea')} />
        {filters.query && <button onClick={() => set('query', '')} aria-label={t('clearFilters')}>
          <Icon name="close" size={14} />
        </button>}
      </label>
      <label className="filter-label">
        {t('district')}
        <select value={filters.district} onChange={(event) => set('district', event.target.value as Filters['district'])}>{(['All', 'Kathmandu', 'Lalitpur', 'Bhaktapur'] as const).map((district) => <option key={district} value={district}>{t(`district.${district}`)}</option>)}</select>
      </label>
      <div className="filter-divider" />
      <span className="filter-label">{t('pollutant')}</span>
      <div className="metric-options">{(['AQI', 'PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO'] as const).map((metric) => <button key={metric} className={filters.metric === metric ? 'selected' : ''} onClick={() => set('metric', metric)} aria-pressed={filters.metric === metric}>{metric === 'AQI' ? 'US AQI' : metric}</button>)}</div>
      <label className="filter-label">
        {t('dataSource')}
        <select value={filters.source} onChange={(event) => set('source', event.target.value as Filters['source'])}>
          <option value="all">{t('all')}</option>
          {(['official', 'community', 'modelled'] as const).map((source) => <option key={source} value={source}>{t(`source.${source}`)}</option>)}
        </select>
      </label>
      <label className="switch-label">
        <span>{t('showAllStations')}</span>
        <input type="checkbox" checked={filters.allStations} onChange={(event) => set('allStations', event.target.checked)} />
        <span className="switch-track" aria-hidden="true" />
      </label>
      <button className="text-button clear-filter" onClick={() => onChange(DEFAULT_FILTERS)}>
        {t('clearFilters')}
        <Icon name="refresh" size={13} />
      </button>
    </div>
  </div>;
}
