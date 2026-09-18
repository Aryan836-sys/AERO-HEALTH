import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Icon, { type IconName } from '../Icon';
import Button from '../Button';
export function LoadingState({ compact = false }: {
  compact?: boolean;
}) {
  const { t } = useTranslation();
  return <div className={`state-view ${compact ? 'state-compact' : ''}`} role="status">
    <span className="spinner" />
    <p>{t('loading')}</p>
  </div>;
}
export function EmptyState({ title, description, icon = 'wind', action }: {
  title: string;
  description?: string;
  icon?: IconName;
  action?: ReactNode;
}) {
  return <div className="state-view">
    <span className="state-icon">
      <Icon name={icon} size={28} />
    </span>
    <h3>{title}</h3>
    {description && <p>{description}</p>}
    {action}
  </div>;
}
export function ErrorState({ message, onRetry }: {
  message: string;
  onRetry?: () => void;
}) {
  const { t } = useTranslation();
  return <div className="state-view error-state" role="alert">
    <Icon name="alert" size={28} />
    <h3>{t('couldNotLoad')}</h3>
    <p>{message}</p>
    {onRetry && <Button variant="secondary" onClick={onRetry}>
      <Icon name="refresh" size={16} />
      {t('retry')}
    </Button>}
  </div>;
}
