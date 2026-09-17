import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import { api } from '../services/api';
import { useAsync } from '../hooks/useAsync';
import type { Pollutant } from '../types/api';
import PageHeader from '../components/common/PageHeader';
import AreaSelect from '../components/common/AreaSelect';
import AqiGauge from '../components/common/AqiGauge';
import Freshness from '../components/common/Freshness';
import ReliabilityBadge from '../components/common/ReliabilityBadge';
import DemoBadge from '../components/common/DemoBadge';
import Icon from '../components/common/Icon';
import SaveButton from '../components/common/SaveButton';
import TrendChart from '../components/charts/TrendChart';
import { ErrorState, LoadingState } from '../components/common/states';
export default function Compare() {
  const { t, i18n } = useTranslation();
  const app = useApp();
  const [a, setA] = useState('ratnapark');
  const [b, setB] = useState('patan');
  const compared = useAsync(`compare:${a}:${b}`, () => api.compare(a, b), a !== b);
  const first = compared.data?.find((area) => area.id === a);
  const second = compared.data?.find((area) => area.id === b);
  const difference = first?.reading && second?.reading ? Math.abs(first.reading.aqi - second.reading.aqi) : null;
  return <div className="page-content">
    <PageHeader eyebrow={t('compare.eyebrow')} title={t('compare.title')} description={t('compare.description')} action={<DemoBadge />} />
    {app.loading ? <LoadingState /> : app.error ? <ErrorState message={app.error} onRetry={app.refresh} /> : <>
      <div className="compare-selectors">
        <AreaSelect id="compare-a" value={a} onChange={setA} label={t('firstArea')} />
        <button className="swap-button" aria-label={t('swap')} onClick={() => { setA(b); setB(a); }}>
          <Icon name="compare" size={23} />
        </button>
        <AreaSelect id="compare-b" value={b} onChange={setB} label={t('secondArea')} />
      </div>
      {a === b ? <p className="notice" role="status">{t('sameArea')}</p> : compared.loading ? <LoadingState /> : compared.error ? <ErrorState message={compared.error} onRetry={compared.reload} /> : <>
        <div className="compare-cards">{[first, second].map((area, index) => area && <section className={`card compare-card compare-card-${index}`} key={area.id}>
          <div className="section-heading">
            <div>
              <p className="eyebrow">{t(`district.${area.district}`)}</p>
              <h2>{i18n.language === 'ne' ? area.nameNe : area.name}</h2>
            </div>
            <SaveButton areaId={area.id} compact />
          </div>
          <AqiGauge value={area.reading?.aqi ?? null} />
          {area.reading ? <div className="current-air-context">
            <ReliabilityBadge reliability={area.reading.reliability} isDemo={area.reading.isDemo} />
            <Freshness date={area.reading.observedAt} isDemo={area.reading.isDemo} />
          </div> : <p className="muted">{t('noStationHelp')}</p>}
        </section>)}</div>
        <div className="comparison-summary">
          <Icon name="compare" size={23} />
          <p>{difference === null ? t('noComparison') : <>
            <strong>{difference} AQI</strong>
            {" "}
            {t('readingDifference')}
          </>}</p>
          <span>{t('comparisonNote')}</span>
        </div>
        {first && second && <>
          <div className="card">
            <TrendChart areaId={a} areaName={first.name} compareId={b} compareName={second.name} />
          </div>
          <section className="card comparison-table">
            <div className="section-heading">
              <h2>{t('airComposition')}</h2>
              <Icon name="activity" />
            </div>
            <div className="data-table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>{t('pollutant')}</th>
                    <th>{first.name}</th>
                    <th>{second.name}</th>
                  </tr>
                </thead>
                <tbody>{(['PM2.5', 'PM10', 'O3', 'NO2', 'SO2', 'CO'] as Pollutant[]).map((pollutant) => <tr key={pollutant}>
                  <th scope="row">
                    {pollutant}
                    <span className="muted small"> {pollutant === 'CO' ? 'mg/m\u00b3' : '\u00b5g/m\u00b3'}</span>
                  </th>
                  <td>{first.reading?.pollutants[pollutant] ?? t('noData')}</td>
                  <td>{second.reading?.pollutants[pollutant] ?? t('noData')}</td>
                </tr>)}</tbody>
              </table>
            </div>
          </section>
        </>}
      </>}
    </>}
  </div>;
}
