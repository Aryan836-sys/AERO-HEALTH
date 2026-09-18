import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import AirMap from '../components/map/AirMap';
import MapFilters, { DEFAULT_FILTERS } from '../components/map/MapFilters';
import PageHeader from '../components/common/PageHeader';
import DemoBadge from '../components/common/DemoBadge';
import AqiIndicator, { AqiLegend } from '../components/common/AqiIndicator';
import Icon from '../components/common/Icon';
import { ButtonLink } from '../components/common/Button';
import { ErrorState, LoadingState, EmptyState } from '../components/common/states';
export default function MapPage() {
  const { t, i18n } = useTranslation();
  const { areas, selectedId, selectArea, loading, error, refresh } = useApp();
  const [filters, setFilters] = useState({ ...DEFAULT_FILTERS, allStations: true });
  const visible = useMemo(() => areas.filter((area) => `${area.name} ${area.nameNe} ${area.district}`.toLowerCase().includes(filters.query.trim().toLowerCase()) && (filters.district === 'All' || area.district === filters.district) && (filters.source === 'all' || area.reading?.reliability === filters.source) && (filters.allStations || area.featured)), [areas, filters]);
  return <div className="page-content">
    <PageHeader eyebrow={t('map.eyebrow')} title={t('map.title')} description={t('map.description')} action={<>
      <ButtonLink to="/compare" variant="secondary">
        <Icon name="compare" size={16} />
        {t('compareAreas')}
      </ButtonLink>
      <DemoBadge />
    </>} />
    {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={refresh} /> : <>
      <div className="map-workspace">
        <aside className="map-sidebar">
          <MapFilters filters={filters} onChange={setFilters} />
          <div className="area-list-heading">
            <strong>{t('mapList')}</strong>
            <span>{visible.length}</span>
          </div>
          <div className="area-list" aria-label={t('mapList')}>{visible.length === 0 ? <EmptyState title={t('noResults')} description={t('searchHint')} /> : visible.map((area) => <div key={area.id} className={`area-list-item ${selectedId === area.id ? 'selected' : ''}`}>
            <button className="area-select-button" onClick={() => selectArea(area.id)} aria-pressed={selectedId === area.id}>
              <span>
                <strong>{i18n.language === 'ne' ? area.nameNe : area.name}</strong>
                <small>{t(`district.${area.district}`)}</small>
              </span>
              <AqiIndicator value={area.reading?.aqi} compact number />
            </button>
            <Link to={`/areas/${area.id}`} aria-label={`${t('viewArea')}: ${area.name}`} className="icon-button">
              <Icon name="arrow-up-right" size={16} />
            </Link>
          </div>)}</div>
        </aside>
        <div className="full-map-panel">
          <AirMap largeBubbles={false} areas={visible} selectedId={selectedId} onSelect={selectArea} metric={filters.metric} />
          <div className="full-map-label">
            <Icon name="pin" size={17} />
            <span>{t('valley')}</span>
            <DemoBadge />
          </div>
          {!visible.length && <div className="map-no-results">
            <strong>{t('noStations')}</strong>
          </div>}
        </div>
      </div>
      <div className="map-footer-strip">
        <AqiLegend detailed />
        <p>
          <Icon name="info" size={14} />
          {t('mapNote')}
        </p>
      </div>
    </>}
  </div>;
}
