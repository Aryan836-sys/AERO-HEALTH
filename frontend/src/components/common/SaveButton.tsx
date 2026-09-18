import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../services/api';
import { errorMessage } from '../../utils/format';
import Icon from './Icon';
import Button from './Button';
export default function SaveButton({ areaId, compact = false }: {
  areaId: string;
  compact?: boolean;
}) {
  const { favorites, refreshUser, userDataLoading } = useApp();
  const { user } = useAuth();
  const { t } = useTranslation();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [busy, setBusy] = useState(false);
  const saved = favorites.includes(areaId);
  async function toggle() {
    if (!user) {
      navigate(`/login?next=${encodeURIComponent(location.pathname)}`);
      return;
    }
    setBusy(true);
    try {
      await api.setFavorite(areaId, !saved);
      refreshUser();
      toast(t(saved ? 'locationRemoved' : 'locationSaved'));
    }
    catch (error) {
      toast(errorMessage(error), 'error');
    }
    finally {
      setBusy(false);
    }
  }
  return <Button variant={saved ? 'mint' : 'secondary'} className={compact ? 'save-icon' : ''} loading={busy} disabled={userDataLoading} onClick={toggle} aria-label={t(saved ? 'unsaveLocation' : 'saveLocation')} aria-pressed={saved}>
    <Icon name="bookmark" size={16} fill={saved ? 'currentColor' : 'none'} />
    {!compact && t(saved ? 'saved' : 'watchlist')}
  </Button>;
}
