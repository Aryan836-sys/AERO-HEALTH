import { useTranslation } from 'react-i18next';
import type { HealthProfile } from '../../types/api';
import { api } from '../../services/api';
import { useAsync } from '../../hooks/useAsync';
import { useApp } from '../../context/AppContext';
import Icon from '../common/Icon';
import AqiIndicator from '../common/AqiIndicator';
import { ButtonLink } from '../common/Button';
import { EmptyState, ErrorState, LoadingState } from '../common/states';
export default function AdvisoryPanel({ areaId, profile: profileOverride, expanded = true }: {
  areaId: string;
  profile?: HealthProfile | null;
  expanded?: boolean;
}) {
  const { t } = useTranslation();
  const app = useApp();
  const profile = profileOverride === undefined ? app.profile : profileOverride;
  const area = app.areas.find((item) => item.id === areaId);
  const result = useAsync(`advisory:${areaId}:${JSON.stringify(profile)}`, () => api.getAdvisory(areaId, profile), !!area?.reading);
  if (!area?.reading)
    return <div className="card advisory-panel">
      <EmptyState icon="info" title={t('noDirectData')} description={t('noStationHelp')} />
    </div>;
  return <section className={`card advisory-panel advisory-risk-${result.data?.level ?? 'low'}`}>
    <div className="section-heading">
      <span className="advisory-icon">
        <Icon name="heart" size={22} />
      </span>
      <span className="eyebrow">{t('explainable')}</span>
    </div>
    <h2>{t(profile ? 'yourAdvisory' : 'genericAdvisory')}</h2>
    {result.loading ? <LoadingState compact /> : result.error ? <ErrorState message={result.error} onRetry={result.reload} /> : result.data && <>
      <span className={`risk-badge risk-${result.data.level}`}>
        <Icon name={result.data.level === 'low' ? 'check-circle' : 'alert'} size={15} />
        {t(`risk.${result.data.level}`)}
      </span>
      <p className="advisory-recommendation">{t(result.data.recommendationKey)}</p>
      {expanded && <div className="advisory-reasons">
        <h3>{t('whyThisAdvice')}</h3>
        {result.data.reasons.map((reason, index) => <p key={`${reason.key}-${index}`}>
          <Icon name="check" size={15} />
          <span>{t(reason.key, reason.values)}</span>
        </p>)}
      </div>}
      <div className="advisory-aqi">
        <span>{t('aqiIndex')}</span>
        <AqiIndicator value={result.data.aqi} number compact />
      </div>
      {expanded && <p className="small muted">{t('riskNote')}</p>}
      {!profile && <ButtonLink to="/profile" variant="secondary">
        {t('createProfile')}
        <Icon name="arrow-up-right" size={15} />
      </ButtonLink>}
    </>}
    <p className="disclaimer">
      <Icon name="info" size={15} />
      <span>{t('medicalDisclaimer')}</span>
    </p>
  </section>;
}
