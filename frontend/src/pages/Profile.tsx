import { useEffect, useState, type FormEvent } from 'react';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import { api, IS_DEMO } from '../services/api';
import { errorMessage } from '../utils/format';
import type { HealthFlag, HealthProfile } from '../types/api';
import PageHeader from '../components/common/PageHeader';
import Icon from '../components/common/Icon';
import Button, { ButtonLink } from '../components/common/Button';
import Modal from '../components/common/Modal';
import { ErrorState, LoadingState } from '../components/common/states';
const CONDITIONS: HealthFlag[] = ['asthma', 'respiratory', 'heart', 'pregnancy', 'outdoorWorker'];
const EMPTY_PROFILE: HealthProfile = { ageGroup: '', conditions: [], activityLevel: '', preferredLanguage: 'en' };
export default function Profile() {
  const { t, i18n } = useTranslation();
  const { profile, userDataLoading, userDataError, refreshUser } = useApp();
  const toast = useToast();
  const [form, setForm] = useState<HealthProfile>(EMPTY_PROFILE);
  const [busy, setBusy] = useState(false);
  const [confirmClear, setConfirmClear] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!userDataLoading)
      setForm(profile ?? EMPTY_PROFILE);
  }, [profile, userDataLoading]);
  function toggleCondition(flag: HealthFlag) {
    setForm((previous) => ({ ...previous, conditions: previous.conditions.includes(flag) ? previous.conditions.filter((item) => item !== flag) : [...previous.conditions, flag] }));
  }
  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError('');
    try {
      await api.saveProfile(form);
      await i18n.changeLanguage(form.preferredLanguage);
      refreshUser();
      toast.success(t('profileSaved'));
    }
    catch (failure) {
      setError(errorMessage(failure));
    }
    finally {
      setBusy(false);
    }
  }
  async function clear() {
    setBusy(true);
    try {
      await api.deleteProfile();
      setForm(EMPTY_PROFILE);
      refreshUser();
      setConfirmClear(false);
      toast.success(t('profileCleared'));
    }
    catch (failure) {
      toast.error(errorMessage(failure));
    }
    finally {
      setBusy(false);
    }
  }
  return <div className="page-content">
    <PageHeader eyebrow={t('profile.eyebrow')} title={t('profile.title')} description={t('profile.description')} action={<ButtonLink variant="secondary" to="/dashboard">
      <Icon name="arrow-left" size={16} />
      {t('nav.dashboard')}
    </ButtonLink>} />
    {userDataLoading ? <LoadingState /> : userDataError ? <ErrorState message={userDataError} onRetry={refreshUser} /> :
      <div className="profile-layout">
        <form onSubmit={(event) => void save(event)} className="card profile-form form-stack">
          <div className="section-heading">
            <div>
              <span className="eyebrow">01 / THE BASICS</span>
              <h2>{t('ageGroup')}</h2>
            </div>
            <span className="subtle-pill">{t('optional')}</span>
          </div>
          <div className="choice-grid" role="group" aria-label={t('ageGroup')}>
            {(['', 'child', 'adult', 'older'] as const).map((age) => <label key={age} className={`choice-card ${form.ageGroup === age ? 'is-selected' : ''}`}>
              <input type="radio" name="ageGroup" value={age} checked={form.ageGroup === age} onChange={() => setForm({ ...form, ageGroup: age })} />
              <span>{t(`age.${age || 'none'}`)}</span>
              {form.ageGroup === age && <Icon name="check-circle" size={17} />}
            </label>)}
          </div>
          <div className="form-section">
            <span className="eyebrow">02 / A LITTLE CONTEXT</span>
            <h2>{t('sensitivities')}</h2>
            <p className="small muted">{t('profileOptional')}</p>
            <div className="condition-grid">{CONDITIONS.map((condition) => <label key={condition} className={`condition-choice ${form.conditions.includes(condition) ? 'is-selected' : ''}`}>
              <input type="checkbox" checked={form.conditions.includes(condition)} onChange={() => toggleCondition(condition)} />
              <span>{t(`condition.${condition}`)}</span>
            </label>)}</div>
          </div>
          <div className="two-column-fields form-section">
            <label className="field">
              {t('activityLevel')}
              <select value={form.activityLevel} onChange={(event) => setForm({ ...form, activityLevel: event.target.value as HealthProfile['activityLevel'] })}>{(['', 'low', 'moderate', 'high'] as const).map((level) => <option value={level} key={level}>{t(`activity.${level || 'none'}`)}</option>)}</select>
            </label>
            <label className="field">
              {t('preferredLanguage')}
              <select value={form.preferredLanguage} onChange={(event) => setForm({ ...form, preferredLanguage: event.target.value as 'en' | 'ne' })}>
                <option value="en">English</option>
                <option value="ne">{'\u0928\u0947\u092a\u093e\u0932\u0940'}</option>
              </select>
            </label>
          </div>
          {error && <p className="inline-error" role="alert">{error}</p>}
          <div className="form-actions">
            <Button type="submit" loading={busy}>
              <Icon name="check" size={17} />
              {t('saveProfile')}
            </Button>
            {profile && <Button variant="ghost" disabled={busy} onClick={() => setConfirmClear(true)}>{t('clearProfile')}</Button>}
          </div>
        </form>
        <aside className="profile-sidebar">
          <section className="soft-card mint-card">
            <span className="icon-disc">
              <Icon name="shield" size={27} />
            </span>
            <h2>{t('profilePrivacyTitle')}</h2>
            <p>{t(IS_DEMO ? 'profilePrivacyBody' : 'profileOptional')}</p>
            <div className="privacy-checks">
              <span>
                <Icon name="check" size={17} />
                {t('profileOptional')}
              </span>
              <span>
                <Icon name="check" size={17} />
                {t('clearProfile')}
              </span>
            </div>
          </section>
          <section className="card">
            <span className="eyebrow">AERO / IN CONTEXT</span>
            <h3>{t('explainable')}</h3>
            <p className="muted small">{t('exampleOnly')}</p>
            <ButtonLink variant="ghost" to="/advisory">
              {t('yourAdvisory')}
              <Icon name="arrow-up-right" size={16} />
            </ButtonLink>
          </section>
        </aside>
      </div>}
    <Modal open={confirmClear} title={t('clearProfileQuestion')} onClose={() => setConfirmClear(false)}>
      <p>{t('clearProfileBody')}</p>
      <div className="form-actions">
        <Button variant="secondary" onClick={() => setConfirmClear(false)}>{t('cancel')}</Button>
        <Button variant="danger" loading={busy} onClick={() => void clear()}>{t('clearProfile')}</Button>
      </div>
    </Modal>
  </div>;
}
