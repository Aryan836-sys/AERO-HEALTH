import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import AirMap from '../components/map/AirMap';
import MapFilters, { DEFAULT_FILTERS } from '../components/map/MapFilters';
import { AqiLegend } from '../components/common/AqiIndicator';
import AqiIndicator from '../components/common/AqiIndicator';
import AqiGauge from '../components/common/AqiGauge';
import TrendChart from '../components/charts/TrendChart';
import PageHeader from '../components/common/PageHeader';
import Icon from '../components/common/Icon';
import { ButtonLink } from '../components/common/Button';
import SaveButton from '../components/common/SaveButton';
import Freshness from '../components/common/Freshness';
import ReliabilityBadge from '../components/common/ReliabilityBadge';
import DemoBadge from '../components/common/DemoBadge';
import { ErrorState, LoadingState } from '../components/common/states';
export default function Home() {
  const { t, i18n } = useTranslation();
  const { areas, loading, error, refresh, selectedId, selectArea } = useApp();
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const selected = areas.find((area) => area.id === selectedId) ?? areas[0];
  const visible = useMemo(() => areas.filter((area) => {
    const match = `${area.name} ${area.nameNe} ${area.district}`.toLowerCase().includes(filters.query.trim().toLowerCase());
    const includeAll = filters.allStations || !!filters.query || filters.district !== 'All' || filters.source !== 'all';
    return match && (filters.district === 'All' || area.district === filters.district) && (filters.source === 'all' || area.reading?.reliability === filters.source) && (includeAll || area.featured);
  }), [areas, filters]);
  const reading = selected?.reading;
  return <div className="page-content home-page">
    <PageHeader eyebrow={t('home.eyebrow')} title={<>
      {t('home.title')}
      {" "}
      <em>{t('home.titleAccent')}</em>
    </>} description={t('home.description')} action={<>
      <div className="weather-glance">
        <span className="weather-sun">
          <Icon name="sun" size={27} />
        </span>
        <div>
          <strong>{reading?.weather.temperature ?? '--'}&deg;<small>C</small></strong>
          <span>
            {t('partlyCloudy')}
            {" "}
            <b>&middot;</b>
            {" "}
            {t('sample')}
          </span>
        </div>
      </div>
      <DemoBadge />
    </>} />
    {loading ? <div className="card">
      <LoadingState />
    </div> : error ? <ErrorState message={error} onRetry={refresh} /> : selected && <>
      <section className="home-map-shell">
        <AirMap areas={visible} selectedId={selectedId} onSelect={selectArea} metric={filters.metric} />
        <MapFilters floating filters={filters} onChange={setFilters} />
        <div className="map-location-pill">
          <span className="pin-disc">
            <Icon name="pin" size={17} />
          </span>
          <div>
            <strong>{t('valley')}</strong>
            <span>
              {t('nepal')}
              {" "}
              <b>&middot;</b>
              {" "}
              {t('readingCount', { count: areas.filter((area) => area.reading).length })}
            </span>
          </div>
          <ButtonLink to="/map" variant="ghost" className="map-open-button" aria-label={t('openMap')}>
            <Icon name="arrow-up-right" size={18} />
          </ButtonLink>
        </div>
        <div className="map-legend-overlay">
          <AqiLegend />
        </div>
        {visible.length === 0 && <div className="map-no-results">
          <Icon name="search" />
          <strong>{t('noResults')}</strong>
          <p>{t('searchHint')}</p>
        </div>}
        <span className="map-data-note">
          <span />
          {t('mapNote')}
        </span>
      </section>
      <div className="home-insights">
        <section className="current-air">
          <div className="section-heading">
            <div>
              <p className="eyebrow">{t('selectedArea')}</p>
              <h2>
                {i18n.language === 'ne' ? selected.nameNe : selected.name}
                <small>{t(`district.${selected.district}`)}</small>
              </h2>
            </div>
            <SaveButton areaId={selected.id} compact />
          </div>
          <AqiGauge value={reading?.aqi ?? null} />
          <div className="current-air-context">{reading ? <>
            <ReliabilityBadge reliability={reading.reliability} isDemo={reading.isDemo} />
            <Freshness date={reading.observedAt} isDemo={reading.isDemo} />
          </> : <p className="small muted">{t('noStationHelp')}</p>}</div>
          <Link className="text-button current-area-link" to={`/areas/${selected.id}`}>
            {t('viewArea')}
            <Icon name="arrow-up-right" size={15} />
          </Link>
        </section>
        <TrendChart areaId={selected.id} areaName={i18n.language === 'ne' ? selected.nameNe : selected.name} />
      </div>
      <div className="section-heading overview-heading">
        <div>
          <p className="eyebrow">{t('exploreValley')}</p>
          <h2>{t('todayOverview')}</h2>
        </div>
        <ButtonLink to="/compare" variant="ghost">
          {t('compareAreas')}
          <Icon name="compare" size={16} />
        </ButtonLink>
      </div>
      <div className="district-cards">{areas.filter((area) => area.featured).map((area) => <section className="district-card" key={area.id}>
        <div className="district-card-top">
          <div className={`district-emblem district-${area.district.toLowerCase()}`}>
            <Icon name="building" size={25} />
          </div>
          <div>
            <Link to={`/areas/${area.id}`}>
              <h3>
                {t(`district.${area.district}`)}
                <Icon name="arrow-up-right" size={14} />
              </h3>
            </Link>
            <p>
              {i18n.language === 'ne' ? area.nameNe : area.name}
              {" "}
              <span>&middot; {t('sample')}</span>
            </p>
          </div>
          <SaveButton areaId={area.id} compact />
        </div>
        <div className="district-card-bottom">
          <div className="district-aqi">
            {area.reading?.aqi}
            <small>US AQI</small>
          </div>
          <AqiIndicator value={area.reading?.aqi} compact />
          <div className="mini-weather"><Icon name="sun" size={17} />{area.reading?.weather.temperature}&deg;</div>
        </div>
      </section>)}</div>
      <div className="home-bottom">
        <section className="breathing-banner">
          <div>
            <span className="eyebrow">AERO / EVERYDAY</span>
            <h2>{t('homeTipTitle')}</h2>
            <p>{t('homeTipBody')}</p>
            <ButtonLink to="/awareness" variant="secondary">
              {t('learnAir')}
              <Icon name="arrow-right" size={16} />
            </ButtonLink>
          </div>
          <div className="breath-orbit" aria-hidden="true">
            <i />
            <i />
            <i />
            <Icon name="wind" size={60} />
          </div>
        </section>
        <section className="community-teaser">
          <span className="icon-disc">
            <Icon name="users" size={24} />
          </span>
          <h2>{t('homeCommunity')}</h2>
          <p>{t('homeCommunityBody')}</p>
          <Link to="/community?compose=1" className="text-button">
            {t('reportConcern')}
            <Icon name="arrow-up-right" size={16} />
          </Link>
        </section>
      </div>
    </>}
  </div>;
}
