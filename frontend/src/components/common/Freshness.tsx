import { useTranslation } from 'react-i18next';
import { formatDate, formatTime } from '../../utils/format';
import Icon from './Icon';
export default function Freshness({ date, isDemo }: {
  date: string;
  isDemo: boolean;
}) {
  const { t, i18n } = useTranslation();
  const stale = !isDemo && Date.now() - Date.parse(date) > 3600000;
  return <span className={`freshness ${stale ? 'stale' : ''}`} title={date}>
    <Icon name="clock" size={12} />
    {isDemo ? t('sample') : stale ? t('stale') : t('updated')}
    <span>{formatDate(date, i18n.language)}, {formatTime(date, i18n.language)} NPT</span>
  </span>;
}
