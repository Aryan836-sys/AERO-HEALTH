import { useTranslation } from 'react-i18next';
import type { PollutionReport } from '../../types/api';
import { useApp } from '../../context/AppContext';
import { formatDate } from '../../utils/format';
import Icon from './Icon';
import Modal from './Modal';
export function ReportStatusBadge({ status }: {
  status: PollutionReport['status'];
}) {
  const { t } = useTranslation();
  return <span className={`status-badge status-${status}`}>
    <Icon name={status === 'verified' ? 'check-circle' : status === 'flagged' ? 'flag' : status === 'rejected' ? 'close' : 'clock'} size={13} />
    {t(`status.${status}`)}
  </span>;
}
export default function ReportDetails({ report, onClose }: {
  report: PollutionReport | null;
  onClose: () => void;
}) {
  const { t } = useTranslation();
  const { areas } = useApp();
  return <Modal open={!!report} title={t('reportDetails')} onClose={onClose}>
    {report && <div className="report-detail">
      <div className="section-heading">
        <span className="eyebrow">{report.id}</span>
        <ReportStatusBadge status={report.status} />
      </div>
      <h3>{t(`report.category.${report.category}`)}</h3>
      <p className="report-description">{report.description}</p>
      {report.photo && <img className="report-photo" src={report.photo} alt={t('attachedReportPhoto')} />}
      <dl className="detail-list">
        <div>
          <dt>{t('location')}</dt>
          <dd>{areas.find((area) => area.id === report.areaId)?.name ?? report.areaId}</dd>
        </div>
        <div>
          <dt>{t('stationCoordinates')}</dt>
          <dd>{report.latitude.toFixed(5)}, {report.longitude.toFixed(5)}</dd>
        </div>
        <div>
          <dt>{t('reportedBy')}</dt>
          <dd>{report.anonymous ? t('anonymousAuthor') : report.author}</dd>
        </div>
        <div>
          <dt>{t('date')}</dt>
          <dd>{formatDate(report.createdAt)}</dd>
        </div>
      </dl>
      <p className="notice">
        <Icon name="info" size={18} />
        {t('reportStatusHelp')}
      </p>
    </div>}
  </Modal>;
}
