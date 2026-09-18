import { useState, type FormEvent } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useApp } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import { api, IS_DEMO } from '../services/api';
import { errorMessage } from '../utils/format';
import { validThreshold } from '../utils/validation';
import type { AlertRule } from '../types/api';
import PageHeader from '../components/common/PageHeader';
import Icon from '../components/common/Icon';
import Button, { ButtonLink } from '../components/common/Button';
import AqiIndicator from '../components/common/AqiIndicator';
import AreaSelect from '../components/common/AreaSelect';
import SaveButton from '../components/common/SaveButton';
import Modal from '../components/common/Modal';
import DemoBadge from '../components/common/DemoBadge';
import AdvisoryPanel from '../components/advisory/AdvisoryPanel';
import TrendChart from '../components/charts/TrendChart';
import { EmptyState, ErrorState, LoadingState } from '../components/common/states';
export default function Dashboard() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const { areas, favorites, alerts, profile, selectedId, selectArea, userDataLoading, userDataError, refreshUser } = useApp();
  const toast = useToast();
  const [watchlistOpen, setWatchlistOpen] = useState(false);
  const [alertOpen, setAlertOpen] = useState(false);
  const [areaId, setAreaId] = useState('');
  const [threshold, setThreshold] = useState(100);
  const [channel, setChannel] = useState<AlertRule['channel']>('in-app');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const savedAreas = areas.filter((area) => favorites.includes(area.id));
  const selected = areas.find((area) => area.id === selectedId && area.reading) ?? areas.find((area) => area.reading);
  function startAlert() {
    if (!savedAreas.length) {
      toast.error(t('saveFirst'));
      setWatchlistOpen(true);
      return;
    }
    setAreaId(savedAreas[0].id);
    setError('');
    setAlertOpen(true);
  }
  async function createAlert(event: FormEvent) {
    event.preventDefault();
    if (!validThreshold(threshold)) {
      setError(t('thresholdInvalid'));
      return;
    }
    setBusy('new');
    setError('');
    try {
      await api.saveAlert({ areaId, threshold, channel, enabled: true });
      refreshUser();
      setAlertOpen(false);
      toast.success(t('alertCreated'));
    }
    catch (failure) {
      setError(errorMessage(failure));
    }
    finally {
      setBusy('');
    }
  }
  async function changeAlert(id: string, remove = false) {
    setBusy(id);
    try {
      if (remove)
        await api.deleteAlert(id);
      else
        await api.toggleAlert(id);
      refreshUser();
      toast.success(t(remove ? 'alertDeleted' : 'alertUpdated'));
    }
    catch (failure) {
      toast.error(errorMessage(failure));
    }
    finally {
      setBusy('');
    }
  }
  return <div className="page-content">
    <PageHeader eyebrow={t('dashboard.eyebrow')} title={t('welcomeUser', { name: user?.name.split(' ')[0] })} description={t('dashboard.description')} action={<DemoBadge />} />
    <section className="dashboard-banner">
      <div>
        <span className="eyebrow">YOUR DAY, WITH A LITTLE MORE CLARITY</span>
        <h2>{t('dashboard.title')}</h2>
        <p>{t('freshPerspectiveBody')}</p>
        <ButtonLink variant="secondary" to="/map">
          {t('openMap')}
          <Icon name="arrow-up-right" size={17} />
        </ButtonLink>
      </div>
      <div className="breath-orbit" aria-hidden="true">
        <i />
        <i />
        <i />
        <Icon name="wind" size={58} />
      </div>
    </section>
    {userDataLoading ? <LoadingState /> : userDataError ? <ErrorState message={userDataError} onRetry={refreshUser} /> : <>
      <div className="stat-grid three-stats">
        <section className="stat-card">
          <span className="icon-disc">
            <Icon name="bookmark" />
          </span>
          <div>
            <p>{t('savedLocations')}</p>
            <strong>{favorites.length}</strong>
          </div>
          <span className="stat-foot">{t('valley')}</span>
        </section>
        <section className="stat-card">
          <span className="icon-disc lavender">
            <Icon name="bell" />
          </span>
          <div>
            <p>{t('activeAlerts')}</p>
            <strong>{alerts.filter((alert) => alert.enabled).length}</strong>
          </div>
          <span className="stat-foot">{t('sample')}</span>
        </section>
        <section className="stat-card">
          <span className="icon-disc peach">
            <Icon name="heart" />
          </span>
          <div>
            <p>{t('profileStatus')}</p>
            <strong className="stat-label">{t(profile ? 'profileAdded' : 'profileNotAdded')}</strong>
          </div>
          <Link to="/profile" className="text-button stat-foot">
            {t('reviewProfile')}
            <Icon name="arrow-up-right" size={14} />
          </Link>
        </section>
      </div>
      <div className="section-heading spaced-heading">
        <div>
          <span className="eyebrow">YOUR PLACES / AT A GLANCE</span>
          <h2>{t('savedLocations')}</h2>
        </div>
        <Button variant="secondary" onClick={() => setWatchlistOpen(true)}>
          <Icon name="plus" size={17} />
          {t('manageWatchlist')}
        </Button>
      </div>
      {savedAreas.length ? <div className="saved-grid">{savedAreas.map((area) => <section className="card saved-card" key={area.id}>
        <div className="section-heading">
          <span className="pin-disc">
            <Icon name="pin" />
          </span>
          <SaveButton areaId={area.id} compact />
        </div>
        <Link to={`/areas/${area.id}`}>
          <h3>{i18n.language === 'ne' ? area.nameNe : area.name}</h3>
        </Link>
        <p className="muted small">{t(`district.${area.district}`)}</p>
        <AqiIndicator value={area.reading?.aqi} />
        <button className="text-button" onClick={() => selectArea(area.id)} disabled={!area.reading}>
          {t('viewTrend')}
          <Icon name="arrow-up-right" size={15} />
        </button>
      </section>)}</div> : <div className="card">
        <EmptyState icon="bookmark" title={t('noFavorites')} description={t('noFavoritesBody')} action={<Button variant="mint" onClick={() => setWatchlistOpen(true)}>
          <Icon name="plus" size={17} />
          {t('addLocation')}
        </Button>} />
      </div>}
      {selected && <div className="dashboard-insights">
        <section className="card">
          <AreaSelect label={t('weeklySummary')} value={selected.id} onChange={selectArea} onlyReadings />
          <TrendChart areaId={selected.id} areaName={selected.name} initialRange="7d" compact />
        </section>
        <AdvisoryPanel areaId={selected.id} />
      </div>}
      {!profile && <section className="profile-nudge">
        <span className="icon-disc lavender">
          <Icon name="heart" size={24} />
        </span>
        <div>
          <h3>{t('noProfile')}</h3>
          <p>{t('noProfileBody')}</p>
        </div>
        <ButtonLink to="/profile" variant="secondary">
          {t('createProfile')}
          <Icon name="arrow-right" size={16} />
        </ButtonLink>
      </section>}
      <section className="card alerts-card" id="alerts">
        <div className="section-heading">
          <div>
            <span className="eyebrow">STAY A LITTLE MORE INFORMED</span>
            <h2>{t('alertsTitle')}</h2>
            <p className="small muted">{t('alertsDescription')}</p>
          </div>
          <Button variant="secondary" onClick={startAlert}>
            <Icon name="plus" size={17} />
            {t('createAlert')}
          </Button>
        </div>
        {!alerts.length ? <EmptyState icon="bell" title={t('noAlerts')} description={t('noAlertsBody')} /> : <div className="alert-list">{alerts.map((alert) => {
          const area = areas.find((item) => item.id === alert.areaId);
          const triggered = area?.reading ? area.reading.aqi >= alert.threshold : false;
          return <div key={alert.id} className={`alert-row ${!alert.enabled ? 'is-paused' : ''}`}>
            <span className={`icon-disc ${triggered ? 'peach' : ''}`}>
              <Icon name="bell" size={20} />
            </span>
            <div className="alert-row-copy">
              <strong>
                {area?.name ?? alert.areaId}
                <span className="subtle-pill">{t(`channel.${alert.channel}`)}</span>
              </strong>
              <p>{t('threshold')}: <b>{alert.threshold}</b><span className="dot-separator">&middot;</span>{t(!area?.reading ? 'noAlertReading' : triggered ? 'aboveThreshold' : 'belowThreshold')}</p>
            </div>
            <button type="button" className={`toggle ${alert.enabled ? 'is-on' : ''}`} role="switch" aria-checked={alert.enabled} aria-label={t(alert.enabled ? 'turnOffAlert' : 'turnOnAlert')} disabled={busy === alert.id} onClick={() => void changeAlert(alert.id)}>
              <span />
            </button>
            <button type="button" className="icon-button danger-text" aria-label={t('delete')} disabled={busy === alert.id} onClick={() => void changeAlert(alert.id, true)}>
              <Icon name="trash" size={18} />
            </button>
          </div>;
        })}</div>}
        {IS_DEMO && <p className="privacy-note">
          <Icon name="info" size={16} />
          {t('alertDemoNotice')}
        </p>}
      </section>
    </>}
    <Modal open={watchlistOpen} title={t('manageWatchlist')} onClose={() => setWatchlistOpen(false)}>
      <div className="watchlist-picker">{areas.map((area) => <div className="watchlist-row" key={area.id}>
        <span>
          <strong>{i18n.language === 'ne' ? area.nameNe : area.name}</strong>
          <small>{t(`district.${area.district}`)}</small>
        </span>
        <AqiIndicator value={area.reading?.aqi} compact />
        <SaveButton areaId={area.id} compact />
      </div>)}</div>
    </Modal>
    <Modal open={alertOpen} title={t('createAlert')} onClose={() => !busy && setAlertOpen(false)}>
      <form className="form-stack" onSubmit={(event) => void createAlert(event)}>
        <label className="field">
          {t('location')}
          <select value={areaId} onChange={(event) => setAreaId(event.target.value)}>{savedAreas.map((area) => <option key={area.id} value={area.id}>{area.name}</option>)}</select>
        </label>
        <label className="field">
          {t('threshold')}
          <input type="number" min="1" max="500" step="1" required value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} />
        </label>
        <label className="field">
          {t('notificationType')}
          <select value={channel} onChange={(event) => setChannel(event.target.value as AlertRule['channel'])}>
            <option value="in-app">{t('channel.in-app')}</option>
            <option value="email">{t('channel.email')}</option>
          </select>
        </label>
        {IS_DEMO && <div className="notice">
          <Icon name="info" />
          {t('alertDemoNotice')}
        </div>}
        {error && <p role="alert" className="inline-error">{error}</p>}
        <Button type="submit" loading={busy === 'new'}>{t('createAlert')}</Button>
      </form>
    </Modal>
  </div>;
}
