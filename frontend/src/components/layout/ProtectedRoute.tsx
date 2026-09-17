import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { LoadingState, EmptyState } from '../common/states';
import { ButtonLink } from '../common/Button';
export default function ProtectedRoute({ admin = false }: {
  admin?: boolean;
}) {
  const { user, ready } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();
  if (!ready)
    return <LoadingState />;
  if (!user)
    return <Navigate replace to={`/login?next=${encodeURIComponent(location.pathname)}`} />;
  if (admin && user.role !== 'admin')
    return <div className="page-content">
      <EmptyState icon="shield" title={t('protectedAdmin')} description={t('protectedAdminBody')} action={<ButtonLink to="/map">{t('openMap')}</ButtonLink>} />
    </div>;
  return <Outlet />;
}
