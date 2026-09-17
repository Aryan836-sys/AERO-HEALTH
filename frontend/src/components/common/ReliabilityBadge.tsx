import { useTranslation } from 'react-i18next';
import type { Reliability } from '../../types/api';
import Icon from './Icon';
export default function ReliabilityBadge({ reliability, isDemo = false }: {
  reliability: Reliability;
  isDemo?: boolean;
}) {
  const { t } = useTranslation();
  return <span className="reliability-badge" title={t(`sourceHelp.${reliability}`)}>
    <Icon name={reliability === 'official' ? 'shield' : reliability === 'community' ? 'users' : 'sparkles'} size={13} />
    {isDemo && `${t('demo')} \u00b7 `}
    {t(`source.${reliability}`)}
  </span>;
}
