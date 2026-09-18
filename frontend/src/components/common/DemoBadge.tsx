import { useTranslation } from 'react-i18next';
import { IS_DEMO } from '../../services/api';
export default function DemoBadge() {
  const { t } = useTranslation();
  return <span className="demo-pill" title={t(IS_DEMO ? 'demoDetails' : 'backendNotice')}>
    <span />
    {t(IS_DEMO ? 'demoMode' : 'liveMode')}
  </span>;
}
