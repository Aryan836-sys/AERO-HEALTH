import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { HealthProfile } from '../types/api';
import { useApp } from '../context/AppContext';
import PageHeader from '../components/common/PageHeader';
import DemoBadge from '../components/common/DemoBadge';
import AreaSelect from '../components/common/AreaSelect';
import Icon from '../components/common/Icon';
import { ButtonLink } from '../components/common/Button';
import AdvisoryPanel from '../components/advisory/AdvisoryPanel';
import AqiIndicator from '../components/common/AqiIndicator';
import { LoadingState, ErrorState } from '../components/common/states';
export default function Advisory() {
  const { t } = useTranslation();
  const { areas, profile, loading, error, refresh } = useApp();
  const [areaId, setAreaId] = useState('ratnapark');
  const [mode, setMode] = useState<'saved' | 'adult' | 'child'>('saved');
  const example: HealthProfile | null = mode === 'saved' ? profile : { ageGroup: mode === 'child' ? 'child' : 'adult', conditions: mode === 'child' ? ['asthma'] : [], activityLevel: 'moderate', preferredLanguage: 'en' };
  return <div className="page-content">
    <PageHeader eyebrow={t('advisory.eyebrow')} title={t('advisory.title')} description={t('advisory.description')} action={<DemoBadge />} />
    {loading ? <LoadingState /> : error ? <ErrorState message={error} onRetry={refresh} /> : <>
      <div className="advisory-page-grid">
        <div>
          <section className="card advisory-controls">
            <span className="icon-disc">
              <Icon name="leaf" size={28} />
            </span>
            <h2>{t('profilePreview')}</h2>
            <p>{t('exampleOnly')}</p>
            <AreaSelect value={areaId} onChange={setAreaId} onlyReadings />
            <div className="profile-example-list">{(['saved', 'adult', 'child'] as const).map((item) => <button key={item} className={mode === item ? 'selected' : ''} onClick={() => setMode(item)} aria-pressed={mode === item}>
              <Icon name={item === 'saved' ? 'user' : item === 'adult' ? 'activity' : 'heart'} size={20} />
              <span>{t(item === 'saved' ? 'useMyProfile' : item === 'adult' ? 'adultExample' : 'childExample')}</span>
              <span className="radio-dot" />
            </button>)}</div>
            {mode === 'saved' && !profile && <div className="notice">
              <p>{t('noProfileForAdvice')}</p>
              <ButtonLink to="/profile" variant="secondary">
                {t('createProfile')}
                <Icon name="arrow-right" size={15} />
              </ButtonLink>
            </div>}
            <div className="advisory-location-summary">
              <Icon name="pin" size={18} />
              <span>{areas.find((area) => area.id === areaId)?.name}</span>
              <AqiIndicator value={areas.find((area) => area.id === areaId)?.reading?.aqi} compact number />
            </div>
          </section>
          <section className="soft-note">
            <Icon name="shield" size={21} />
            <div>
              <h3>{t('profilePrivacyTitle')}</h3>
              <p>{t('profilePrivacyBody')}</p>
            </div>
          </section>
        </div>
        <AdvisoryPanel areaId={areaId} profile={example} />
      </div>
      <section className="explanation-banner">
        <Icon name="sparkles" size={30} />
        <div>
          <h2>{t('howWorks')}</h2>
          <p>{t('howWorksBody')}</p>
        </div>
        <ButtonLink to="/awareness" variant="secondary">
          {t('learnMore')}
          <Icon name="arrow-up-right" size={15} />
        </ButtonLink>
      </section>
    </>}
  </div>;
}
