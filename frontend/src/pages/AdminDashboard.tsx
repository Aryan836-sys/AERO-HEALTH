import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useApp } from '../context/AppContext';
import { useToast } from '../context/ToastContext';
import { useAsync } from '../hooks/useAsync';
import { api, IS_DEMO } from '../services/api';
import { errorMessage, formatDate } from '../utils/format';
import type { PollutionReport, ReportStatus } from '../types/api';
import PageHeader from '../components/common/PageHeader';
import Icon from '../components/common/Icon';
import Button from '../components/common/Button';
import ReportDetails, { ReportStatusBadge } from '../components/common/ReportDetails';
import { EmptyState, ErrorState, LoadingState } from '../components/common/states';
export default function AdminDashboard() {
  const { t } = useTranslation();
  const { areas } = useApp();
  const toast = useToast();
  const [filter, setFilter] = useState<ReportStatus | 'all'>('unverified');
  const [busy, setBusy] = useState('');
  const [detail, setDetail] = useState<PollutionReport | null>(null);
  const data = useAsync('admin', async () => {
    const [reports, stats] = await Promise.all([api.getReports(), api.getAdminStats()]);
    return { reports, stats };
  });
  async function moderate(id: string, status: ReportStatus) {
    setBusy(id);
    try {
      await api.moderateReport(id, status);
      data.reload();
      toast.success(t('moderated'));
    }
    catch (failure) {
      toast.error(errorMessage(failure));
    }
    finally {
      setBusy('');
    }
  }
  const reports = data.data?.reports.filter((report) => filter === 'all' || report.status === filter) ?? [];
  const stats = data.data?.stats;
  return <div className="page-content">
    <PageHeader eyebrow={t('admin.eyebrow')} title={t('admin.title')} description={t('admin.description')} action={<span className="admin-role-pill">
      <Icon name="shield" size={17} />
      {t('moderator')}
    </span>} />
    {IS_DEMO && <div className="notice">
      <Icon name="shield" size={20} />
      {t('adminNotice')}
    </div>}
    {data.loading ? <LoadingState /> : data.error ? <ErrorState message={data.error} onRetry={data.reload} /> : <>
      <div className="stat-grid four-stats">{([
        ['totalUsers', stats?.users, 'users'], ['totalReports', stats?.reports, 'file'],
        ['pendingReports', stats?.pending, 'clock'], ['flaggedReports', stats?.flagged, 'flag'],
      ] as const).map(([label, value, icon], index) => <section className="stat-card" key={label}>
        <span className={`icon-disc ${index % 2 ? 'lavender' : ''}`}>
          <Icon name={icon} size={22} />
        </span>
        <div>
          <p>{t(label)}</p>
          <strong>{value ?? 0}</strong>
        </div>
      </section>)}</div>
      <section className="card report-breakdown">
        <div className="section-heading">
          <div>
            <span className="eyebrow">AERO / COMMUNITY SNAPSHOT</span>
            <h2>{t('reportsByCategory')}</h2>
          </div>
          <span className="subtle-pill">{t(IS_DEMO ? 'sample' : 'allReports')}</span>
        </div>
        <div className="category-bars">{(['dust', 'burning', 'traffic', 'industrial', 'other'] as const).map((category) => {
          const count = data.data?.reports.filter((report) => report.category === category).length ?? 0;
          const total = data.data?.reports.length || 1;
          return <div key={category}>
            <div className="category-bar-title">
              <span>{t(`report.category.${category}`)}</span>
              <strong>{count}</strong>
            </div>
            <div className="category-track" aria-hidden="true">
              <span style={{ width: `${count / total * 100}%` }} />
            </div>
          </div>;
        })}</div>
      </section>
      <section className="card moderation-card">
        <div className="section-heading">
          <div>
            <span className="eyebrow">AERO / MODERATION</span>
            <h2>{t('moderationQueue')}</h2>
          </div>
          <Button variant="ghost" onClick={data.reload}>
            <Icon name="refresh" size={16} />
            {t('refresh')}
          </Button>
        </div>
        <div className="segmented status-tabs" aria-label={t('status')}>{(['unverified', 'verified', 'flagged', 'rejected', 'all'] as const).map((status) => <button type="button" key={status} className={filter === status ? 'active' : ''} aria-pressed={filter === status} onClick={() => setFilter(status)}>{t(status === 'all' ? 'allReports' : `status.${status}`)}</button>)}</div>
        {reports.length ? <div className="moderation-list">{reports.map((report) => <article className="moderation-row" key={report.id}>
          <div className="moderation-copy">
            <div className="section-heading">
              <span className="eyebrow">{report.id}</span>
              <ReportStatusBadge status={report.status} />
            </div>
            <h3>{t(`report.category.${report.category}`)}</h3>
            <p>{report.description}</p>
            <div className="report-card-meta">
              <span>
                <Icon name="pin" size={14} />
                {areas.find((area) => area.id === report.areaId)?.name}
              </span>
              <span>{formatDate(report.createdAt)}</span>
              <button type="button" className="text-button" onClick={() => setDetail(report)}>{t('viewDetails')}</button>
            </div>
          </div>
          <div className="moderation-actions">
            <Button variant="mint" disabled={!!busy || report.status === 'verified'} onClick={() => void moderate(report.id, 'verified')}>
              <Icon name="check-circle" size={16} />
              {t('verify')}
            </Button>
            <Button variant="secondary" disabled={!!busy || report.status === 'flagged'} onClick={() => void moderate(report.id, 'flagged')}>
              <Icon name="flag" size={16} />
              {t('flag')}
            </Button>
            <Button variant="ghost" className="danger-text" disabled={!!busy || report.status === 'rejected'} onClick={() => void moderate(report.id, 'rejected')}>
              <Icon name="close" size={16} />
              {t('reject')}
            </Button>
          </div>
        </article>)}</div> : <EmptyState icon="check-circle" title={t('emptyQueue')} description={t('emptyQueueBody')} />}
      </section>
    </>}
    <ReportDetails report={detail} onClose={() => setDetail(null)} />
  </div>;
}
