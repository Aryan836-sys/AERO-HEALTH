import { useEffect, useRef, useState, type FormEvent } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { useAsync } from '../hooks/useAsync';
import { api, IS_DEMO } from '../services/api';
import type { PollutionReport, ReportCategory, ReportStatus } from '../types/api';
import { errorMessage, formatDate } from '../utils/format';
import { isInValley } from '../utils/geo';
import { validatePhoto } from '../utils/validation';
import PageHeader from '../components/common/PageHeader';
import Icon from '../components/common/Icon';
import Button from '../components/common/Button';
import AreaSelect from '../components/common/AreaSelect';
import AirMap from '../components/map/AirMap';
import ReportDetails, { ReportStatusBadge } from '../components/common/ReportDetails';
import { EmptyState, ErrorState, LoadingState } from '../components/common/states';
export const REPORT_CATEGORIES: ReportCategory[] = ['dust', 'burning', 'traffic', 'industrial', 'other'];
export const REPORT_STATUSES: ReportStatus[] = ['unverified', 'verified', 'rejected', 'flagged'];
export default function ReportPage() {
  const { t } = useTranslation();
  const { areas, loading: areasLoading, error: areasError, refresh } = useApp();
  const { user } = useAuth();
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const compose = params.get('compose') === '1';
  const reports = useAsync('community-reports', api.getReports);
  const [filterArea, setFilterArea] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterCategory, setFilterCategory] = useState('all');
  const [detail, setDetail] = useState<PollutionReport | null>(null);
  const [category, setCategory] = useState<ReportCategory | ''>('');
  const [description, setDescription] = useState('');
  const [areaId, setAreaId] = useState('ratnapark');
  const [point, setPoint] = useState<[
    number,
    number
  ]>([27.7067, 85.3153]);
  const [anonymous, setAnonymous] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [error, setError] = useState('');
  const [photoError, setPhotoError] = useState('');
  const [progress, setProgress] = useState(0);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!file) {
      setPreview('');
      return;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  useEffect(() => {
    const update = () => reports.reload();
    window.addEventListener('aero:data-changed', update);
    return () => window.removeEventListener('aero:data-changed', update);
  }, [reports.reload]);
  function changeArea(id: string) {
    setAreaId(id);
    const area = areas.find((item) => item.id === id);
    if (area)
      setPoint([area.latitude, area.longitude]);
  }
  function chooseFile(next: File | undefined) {
    if (!next)
      return;
    const invalid = validatePhoto(next);
    setPhotoError(invalid ? t(invalid) : '');
    if (!invalid)
      setFile(next);
    if (fileRef.current)
      fileRef.current.value = '';
  }
  function openCompose() { setSent(false); setParams({ compose: '1' }); }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError('');
    if (!category || description.trim().length < 15 || description.trim().length > 1500 || !isInValley(...point)) {
      setError(t('reportValidation'));
      return;
    }
    if (photoError) {
      setError(photoError);
      return;
    }
    const data = new FormData();
    data.set('category', category);
    data.set('description', description.trim());
    data.set('areaId', areaId);
    data.set('latitude', String(point[0]));
    data.set('longitude', String(point[1]));
    data.set('anonymous', String(anonymous || !user));
    if (file)
      data.set('photo', file);
    setBusy(true);
    setProgress(0);
    try {
      await api.submitReport(data, setProgress);
      setSent(true);
      setDescription('');
      setCategory('');
      setFile(null);
      reports.reload();
      toast.success(t('reportSent'));
    }
    catch (failure) {
      setError(errorMessage(failure));
    }
    finally {
      setBusy(false);
    }
  }
  const visible = (reports.data ?? []).filter((report) => (filterArea === 'all' || report.areaId === filterArea) &&
    (filterStatus === 'all' || report.status === filterStatus) &&
    (filterCategory === 'all' || report.category === filterCategory));
  return <div className="page-content">
    <PageHeader eyebrow={t('community.eyebrow')} title={t('community.title')} description={t('community.description')} action={<Button variant={compose ? 'secondary' : 'primary'} onClick={() => compose ? setParams({}) : openCompose()}>
      <Icon name={compose ? 'arrow-left' : 'plus'} size={17} />
      {t(compose ? 'browseReports' : 'newReport')}
    </Button>} />
    {IS_DEMO && <p className="notice community-notice">
      <Icon name="info" size={19} />
      {t('communityNotice')}
    </p>}
    {compose ? sent ? <section className="card report-success">
      <span className="success-orbit">
        <Icon name="check" size={38} />
      </span>
      <span className="eyebrow">AERO / COMMUNITY</span>
      <h2>{t('reportThanks')}</h2>
      <p>{t(IS_DEMO ? 'reportThanksBody' : 'reportReceived')}</p>
      <ReportStatusBadge status="unverified" />
      <Button onClick={() => setParams({})}>
        {t('viewReports')}
        <Icon name="arrow-right" size={17} />
      </Button>
    </section> :
      <div className="report-compose-layout">
        <form className="card report-form form-stack" onSubmit={(event) => void submit(event)} noValidate>
          <div>
            <span className="eyebrow">01 / YOUR OBSERVATION</span>
            <h2>{t('newReport')}</h2>
          </div>
          <fieldset className="category-fieldset">
            <legend>{t('reportCategory')}</legend>
            <div className="category-choices">{REPORT_CATEGORIES.map((item) => <label className={`category-choice ${category === item ? 'is-selected' : ''}`} key={item}>
              <input type="radio" name="report-category" value={item} checked={category === item} onChange={() => setCategory(item)} />
              <Icon name={item === 'dust' ? 'wind' : item === 'traffic' ? 'activity' : item === 'burning' ? 'sun' : item === 'industrial' ? 'building' : 'dots'} size={18} />
              <span>{t(`report.category.${item}`)}</span>
            </label>)}</div>
          </fieldset>
          <label className="field">
            {t('reportDescription')}
            <textarea rows={5} maxLength={1500} minLength={15} required value={description} onChange={(event) => setDescription(event.target.value)} aria-describedby="description-hint" />
            <span className="field-counter">
              <span id="description-hint">{t('reportDescriptionHint')}</span>
              <b>{description.length}/1500</b>
            </span>
          </label>
          <div className="form-section">
            <span className="eyebrow">02 / PIN THE PLACE</span>
            <h3>{t('reportLocation')}</h3>
            {areasLoading ? <LoadingState compact /> : areasError ? <ErrorState message={areasError} onRetry={refresh} /> : <>
              <AreaSelect value={areaId} onChange={changeArea} label={t('nearestArea')} />
              <p className="field-help">{t('pickLocationHint')}</p>
              <div className="report-map">
                <AirMap areas={areas.filter((area) => area.featured)} selectedId={areaId} onSelect={changeArea} onPick={(lat, lng) => setPoint([lat, lng])} picked={point} largeBubbles={false} />
              </div>
              <div className="two-column-fields">
                <label className="field">
                  {t('latitude')}
                  <input type="number" step="0.00001" value={Number.isFinite(point[0]) ? point[0] : ''} onChange={(event) => setPoint([event.target.value === '' ? NaN : Number(event.target.value), point[1]])} />
                </label>
                <label className="field">
                  {t('longitude')}
                  <input type="number" step="0.00001" value={Number.isFinite(point[1]) ? point[1] : ''} onChange={(event) => setPoint([point[0], event.target.value === '' ? NaN : Number(event.target.value)])} />
                </label>
              </div>
            </>}
          </div>
          <div className="form-section">
            <span className="eyebrow">03 / AN OPTIONAL DETAIL</span>
            <h3>{t('attachPhoto')}</h3>
            <div className={`photo-dropzone ${preview ? 'has-preview' : ''}`} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); chooseFile(event.dataTransfer.files[0]); }}>
              {preview ? <>
                <img src={preview} alt={t('photoPreview')} />
                <Button variant="secondary" onClick={() => { setFile(null); setPhotoError(''); }}>
                  <Icon name="trash" size={16} />
                  {t('removePhoto')}
                </Button>
              </> : <>
                <span className="icon-disc lavender">
                  <Icon name="upload" size={24} />
                </span>
                <p>{t('photoHint')}</p>
                <Button variant="secondary" onClick={() => fileRef.current?.click()}>{t('choosePhoto')}</Button>
              </>}
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(event) => chooseFile(event.target.files?.[0])} aria-label={t('choosePhoto')} />
            </div>
            {photoError && <p className="field-error" role="alert">
              {photoError}
              <button type="button" className="text-button" onClick={() => setPhotoError('')}>{t('dismiss')}</button>
            </p>}
          </div>
          <label className="checkbox-row">
            <input type="checkbox" checked={anonymous || !user} disabled={!user} onChange={(event) => setAnonymous(event.target.checked)} />
            <span>
              <strong>{t('anonymous')}</strong>
              <small>{t('anonymousHint')}</small>
            </span>
            <Icon name="shield" size={20} />
          </label>
          {error && <p className="inline-error" role="alert">
            <Icon name="alert" />
            {error}
          </p>}
          {busy && <div className="upload-progress" role="status">
            <label>
              {t('uploading')}
              <strong>{Math.round(progress)}%</strong>
            </label>
            <progress max={100} value={progress} />
          </div>}
          <Button type="submit" loading={busy} disabled={areasLoading || !!areasError}>
            {t(IS_DEMO ? 'submitReport' : 'submitRealReport')}
            <Icon name="arrow-right" size={17} />
          </Button>
        </form>
        <aside className="report-sidebar">
          <section className="soft-card mint-card">
            <span className="icon-disc">
              <Icon name="users" size={28} />
            </span>
            <h2>{t('homeCommunity')}</h2>
            <p>{t('homeCommunityBody')}</p>
            <div className="report-steps">
              <div>
                <b>01</b>
                <span>{t('reportCategory')}</span>
              </div>
              <div>
                <b>02</b>
                <span>{t('reportLocation')}</span>
              </div>
              <div>
                <b>03</b>
                <span>{t('status.unverified')}</span>
              </div>
            </div>
          </section>
          <section className="card">
            <Icon name="shield" size={23} />
            <h3>{t('privacy')}</h3>
            <p className="small muted">{t('reportDescriptionHint')}</p>
            <p className="small muted">{t('reportStatusHelp')}</p>
          </section>
        </aside>
      </div> : <>
      <div className="community-heading">
        <div>
          <span className="eyebrow">LISTENING TO THE VALLEY</span>
          <h2>
            {t('nearbyReports')}
            <span className="count-pill">{visible.length}</span>
          </h2>
        </div>
        <div className="report-filters">
          <label className="field compact-field">
            <span>{t('location')}</span>
            <select value={filterArea} onChange={(event) => setFilterArea(event.target.value)}>
              <option value="all">{t('allAreas')}</option>
              {areas.map((area) => <option key={area.id} value={area.id}>{area.name}</option>)}
            </select>
          </label>
          <label className="field compact-field">
            <span>{t('status')}</span>
            <select value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)}>
              <option value="all">{t('allStatuses')}</option>
              {REPORT_STATUSES.map((status) => <option key={status} value={status}>{t(`status.${status}`)}</option>)}
            </select>
          </label>
          <label className="field compact-field">
            <span>{t('category')}</span>
            <select value={filterCategory} onChange={(event) => setFilterCategory(event.target.value)}>
              <option value="all">{t('allCategories')}</option>
              {REPORT_CATEGORIES.map((item) => <option key={item} value={item}>{t(`report.category.${item}`)}</option>)}
            </select>
          </label>
        </div>
      </div>
      {reports.loading ? <LoadingState /> : reports.error ? <ErrorState message={reports.error} onRetry={reports.reload} /> : visible.length ? <div className="reports-grid">{visible.map((report) => <article className="card report-card" key={report.id}>
        <div className="section-heading">
          <span className={`icon-disc ${report.category === 'burning' ? 'peach' : 'lavender'}`}>
            <Icon name={report.category === 'traffic' ? 'activity' : report.category === 'industrial' ? 'building' : 'wind'} size={22} />
          </span>
          <ReportStatusBadge status={report.status} />
        </div>
        <span className="eyebrow">{report.id}</span>
        <h3>{t(`report.category.${report.category}`)}</h3>
        <p className="report-card-description">{report.description}</p>
        <div className="report-card-meta">
          <span>
            <Icon name="pin" size={15} />
            {areas.find((area) => area.id === report.areaId)?.name}
          </span>
          <span>
            <Icon name="clock" size={14} />
            {formatDate(report.createdAt)}
          </span>
        </div>
        <div className="report-card-footer">
          <span>{report.anonymous ? t('anonymousAuthor') : report.author}</span>
          <button type="button" className="text-button" onClick={() => setDetail(report)}>
            {t('viewDetails')}
            <Icon name="arrow-up-right" size={16} />
          </button>
        </div>
      </article>)}</div> : <div className="card">
        <EmptyState icon="users" title={t('noReports')} description={t('noReportsBody')} action={<Button onClick={openCompose}>{t('newReport')}</Button>} />
      </div>}
    </>}
    <ReportDetails report={detail} onClose={() => setDetail(null)} />
  </div>;
}
