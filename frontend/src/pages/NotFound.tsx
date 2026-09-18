import { useTranslation } from 'react-i18next';
import Icon from '../components/common/Icon';
import { ButtonLink } from '../components/common/Button';
export default function NotFound() {
  const { t } = useTranslation();
  return <div className="page-content not-found">
    <span className="not-found-number">404</span>
    <div className="breath-orbit" aria-hidden="true">
      <i />
      <i />
      <i />
      <Icon name="wind" size={60} />
    </div>
    <h1>{t('notFound')}</h1>
    <p>{t('notFoundBody')}</p>
    <ButtonLink to="/">
      {t('backHome')}
      <Icon name="arrow-right" size={17} />
    </ButtonLink>
  </div>;
}
