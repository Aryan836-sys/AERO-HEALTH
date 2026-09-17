import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import type { Pollutant } from '../types/api';
import { nearestStation } from '../utils/geo';
import PageHeader from '../components/common/PageHeader';
import Icon from '../components/common/Icon';
import Button, { ButtonLink } from '../components/common/Button';
import SaveButton from '../components/common/SaveButton';
import AqiGauge from '../components/common/AqiGauge';
import DemoBadge from '../components/common/DemoBadge';
import Freshness from '../components/common/Freshness';
import ReliabilityBadge from '../components/common/ReliabilityBadge';
import TrendChart from '../components/charts/TrendChart';
import AirMap from '../components/map/AirMap';
import AdvisoryPanel from '../components/advisory/AdvisoryPanel';
import { EmptyState, ErrorState, LoadingState } from '../components/common/states';
export default function AreaDetail() {
  const { id } = useParams();
  const { areas, loading, error, refresh } = useApp();
  const { t, i18n } = useTranslation();
  const toast = useToast();
  const area = areas.find((item) => item.id === id);
  const reading = area?.reading;
  if (loading)
    return <LoadingState />;
  if (error)
    return <ErrorState message={error} onRetry={refresh} />;
  if (!area)
    return <EmptyState title={t('areaNotFound')} action={<ButtonLink to="/map">{t('backToMap')}</ButtonLink>} />;
  const nearest = !reading ? nearestStation(area, areas) : null;
  const name = i18n.language === 'ne' ? area.nameNe : area.name;
  const share = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      toast(t('linkCopied'));
    }
    catch {
      toast(t('copyFailed'), 'info');
    }
  };
  return <div className="page-content">
    <Link to="/map" className="breadcrumb">
      <Icon name="arrow-left" size={15} />
      {t('backToMap')}
    </Link>
    <PageHeader eyebrow={`${t('area.eyebrow')} / ${t(`district.${area.district}`)}`} title={<>
      {name}
      <span className="heading-location">
        <Icon name="pin" size={21} />
      </span>
    </>} description={t('area.description')} action={<>
      <SaveButton areaId={area.id} />
      <Button variant="secondary" onClick={share}>
        <Icon name="external" size={16} />
        {t('share')}
      </Button>
      <DemoBadge />
    </>} />
    {!reading && <section className="no-data-banner">
      <span className="icon-disc">
        <Icon name="info" />
      </span>
      <div>
        <h2>{t('noDirectData')}</h2>
        <p>{t('noStationHelp')}</p>
        {nearest && <p>{t('nearestStation')}: <strong>{nearest.area.name}</strong> &middot; {nearest.distance.toFixed(1)} km {t('away')}</p>}
      </div>
      {nearest && <ButtonLink to={`/areas/${nearest.area.id}`} variant="secondary">
        {t('nearbyContext')}
        <Icon name="arrow-up-right" size={16} />
      </ButtonLink>}
    </section>}
    <div className="area-overview-grid">
      <section className="card area-aqi-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t('currentReading')}</p>
            <h2>{name}</h2>
          </div>
          <span className="icon-disc small-disc">
            <Icon name="wind" />
          </span>
        </div>
        <AqiGauge value={reading?.aqi ?? null} />
        {reading && <div className="current-air-context">
          <ReliabilityBadge reliability={reading.reliability} isDemo={reading.isDemo} />
          <Freshness date={reading.observedAt} isDemo={reading.isDemo} />
        </div>}
      </section>
      <section className="card pollutants-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">{t('pollutants')}</p>
            <h2>{t('airComposition')}</h2>
          </div>
          <Icon name="activity" size={24} />
        </div>
        <div className="pollutant-grid">{(['PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO'] as Pollutant[]).map((pollutant, index) => <div className={`pollutant-card pollutant-${index}`} key={pollutant}>
          <div>
            <span className="pollutant-orbit" aria-hidden="true">
              <i />
              <i />
              <i />
            </span>
            <span>{pollutant}</span>
          </div>
          <strong>
            {reading?.pollutants[pollutant] ?? '--'}
            <small>{pollutant === 'CO' ? 'mg/m\u00b3' : '\u00b5g/m\u00b3'}</small>
          </strong>
        </div>)}</div>
        <p className="small muted">
          <Icon name="info" size={12} />
          {" "}
          {t('pollutantNote')}
        </p>
      </section>
    </div>
    {reading && <div className="weather-strip">
      <div>
        <Icon name="sun" size={23} />
        <span>
          {t('temperature')}
          <strong>{reading.weather.temperature}&deg;C</strong>
        </span>
      </div>
      <div>
        <Icon name="drop" size={23} />
        <span>
          {t('humidity')}
          <strong>{reading.weather.humidity}%</strong>
        </span>
      </div>
      <div>
        <Icon name="wind" size={23} />
        <span>
          {t('wind')}
          <strong>{reading.weather.windSpeed} km/h <small>{reading.weather.windDirection}</small></strong>
        </span>
      </div>
      <div>
        <Icon name="pin" size={23} />
        <span>
          {t('stationCoordinates')}
          <strong>{area.latitude.toFixed(3)} N, {area.longitude.toFixed(3)} E</strong>
        </span>
      </div>
    </div>}
    <div className="area-insights">
      <div className="card">
        <TrendChart areaId={area.id} areaName={name} />
      </div>
      <AdvisoryPanel areaId={area.id} />
    </div>
    <div className="source-map-grid">
      <section className="card source-card">
        <p className="eyebrow">{t('sourceLabel')}</p>
        <h2>{t('sourceGuideTitle')}</h2>
        <p>{t('sourceExplanation')}</p>
        {reading && <>
          <div className="source-line">
            <Icon name="shield" size={19} />
            <span>{reading.source}</span>
          </div>
          <Freshness date={reading.observedAt} isDemo={reading.isDemo} />
        </>}
        <Link to="/awareness" className="text-button">
          {t('learnMore')}
          <Icon name="arrow-up-right" size={15} />
        </Link>
      </section>
      <section className="area-mini-map">
        <AirMap areas={[area]} selectedId={area.id} largeBubbles={false} />
        <span className="mini-map-label">
          <Icon name="pin" size={14} />
          {t('geographicContext')}
        </span>
      </section>
    </div>
  </div>;
}
