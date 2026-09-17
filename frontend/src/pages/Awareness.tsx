import { useState, type CSSProperties } from 'react';
import { useTranslation } from 'react-i18next';
import PageHeader from '../components/common/PageHeader';
import Icon, { type IconName } from '../components/common/Icon';
import { AqiLegend } from '../components/common/AqiIndicator';
import { AQI_CATEGORIES } from '../utils/aqi';
import Modal from '../components/common/Modal';
import Button, { ButtonLink } from '../components/common/Button';
const GUIDES: {
  key: string;
  icon: IconName;
  tone: string;
}[] = [
    { key: 'aqi', icon: 'activity', tone: 'mint' },
    { key: 'pollutant', icon: 'wind', tone: 'lavender' },
    { key: 'source', icon: 'shield', tone: 'peach' },
  ];
export default function Awareness() {
  const { t } = useTranslation();
  const [guide, setGuide] = useState<string | null>(null);
  return <div className="page-content">
    <PageHeader eyebrow={t('awareness.eyebrow')} title={t('awareness.title')} description={t('awareness.description')} action={<ButtonLink to="/map" variant="secondary">
      {t('openMap')}
      <Icon name="arrow-up-right" size={16} />
    </ButtonLink>} />
    <section className="awareness-hero">
      <div>
        <span className="eyebrow">UNDERSTANDING AIR / THE AERO WAY</span>
        <h2>{t('aqiGuideTitle')}</h2>
        <p>{t('aqiGuideBody')}</p>
        <Button variant="secondary" onClick={() => setGuide('aqi')}>
          {t('readGuide')}
          <Icon name="arrow-right" size={17} />
        </Button>
      </div>
      <div className="aqi-spectrum-art" aria-hidden="true">
        {AQI_CATEGORIES.map((category, index) => <span style={{ '--band-color': category.color, '--band-index': index } as CSSProperties} key={category.key}>
          <i />
        </span>)}
        <div className="spectrum-art-center">
          <Icon name="wind" size={45} />
          <small>AIR, EXPLAINED.</small>
        </div>
      </div>
    </section>
    <div className="education-grid">{GUIDES.map(({ key, icon, tone }, index) => <article className="card education-card" key={key}>
      <div className="section-heading">
        <span className={`icon-disc ${tone}`}>
          <Icon name={icon} size={26} />
        </span>
        <span className="article-number">0{index + 1}</span>
      </div>
      <h2>{t(`${key}GuideTitle`)}</h2>
      <p>{t(`${key}GuideBody`)}</p>
      <Button variant="ghost" onClick={() => setGuide(key)}>
        {t('readGuide')}
        <Icon name="arrow-up-right" size={16} />
      </Button>
    </article>)}</div>
    <section className="card scale-explainer">
      <div className="section-heading">
        <div>
          <span className="eyebrow">SIX CATEGORIES. NO GUESSWORK.</span>
          <h2>{t('aqiScale')}</h2>
        </div>
        <span className="subtle-pill">US EPA AQI</span>
      </div>
      <AqiLegend detailed />
      <p className="muted small">{t('designNote')}</p>
    </section>
    <section className="faq-section">
      <div>
        <span className="eyebrow">CURIOUS? GOOD.</span>
        <h2>{t('faq')}</h2>
        <p>{t('articleLanguage')}</p>
      </div>
      <div className="faq-list">{[1, 2, 3, 4].map((number) => <details key={number}>
        <summary>
          {t(`faq${number}`)}
          <Icon name="plus" size={18} />
        </summary>
        <p>{t(`faq${number}a`)}</p>
      </details>)}</div>
    </section>
    <section className="source-strip">
      <Icon name="book" size={24} />
      <div>
        <strong>{t('educationSource')}</strong>
        <p>{t('articleLanguage')}</p>
      </div>
      <a className="text-button" href="https://www.airnow.gov/aqi/aqi-basics/" target="_blank" rel="noreferrer">
        {t('openAirNow')}
        <Icon name="external" size={17} />
      </a>
    </section>
    <Modal open={!!guide} title={guide ? t(`${guide}GuideTitle`) : ''} onClose={() => setGuide(null)} wide>
      {guide && <div className="education-article">
        <p className="article-intro">{t(`${guide}GuideBody`)}</p>
        {guide === 'aqi' ? <>
          <AqiLegend detailed />
          <p>{t('faq3a')}</p>
          <p>{t('designNote')}</p>
        </> : guide === 'pollutant' ? <>
          <div className="pollutant-glossary">{[['PM2.5', 'Fine particulate matter'], ['PM10', 'Inhalable particulate matter'], ['O3', 'Ozone'], ['NO2', 'Nitrogen dioxide'], ['SO2', 'Sulfur dioxide'], ['CO', 'Carbon monoxide']].map(([label, name]) => <div key={label}>
            <strong>{label}</strong>
            <span>{name}</span>
          </div>)}</div>
          <p>{t('airCompositionNote')}</p>
        </> : <>
          <div className="source-comparison">{['official', 'community', 'modelled'].map((source) => <div key={source}>
            <Icon name={source === 'official' ? 'shield' : source === 'community' ? 'users' : 'sparkles'} />
            <strong>{t(`source.${source}`)}</strong>
            <p>{t(`sourceHelp.${source}`)}</p>
          </div>)}</div>
          <p>{t('faq2a')}</p>
        </>}
        <p className="notice">
          <Icon name="info" size={18} />
          {t('medicalDisclaimer')}
        </p>
        <a className="text-button" href="https://www.airnow.gov/aqi/aqi-basics/" target="_blank" rel="noreferrer">
          {t('openAirNow')}
          <Icon name="external" size={16} />
        </a>
      </div>}
    </Modal>
  </div>;
}
