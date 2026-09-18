import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import { useApp } from '../../context/AppContext';
import { useToast } from '../../context/ToastContext';
import { IS_DEMO } from '../../services/api';
import { errorMessage } from '../../utils/format';
import Icon, { type IconName } from '../common/Icon';
import Logo from '../common/Logo';
import Modal from '../common/Modal';
import { ButtonLink } from '../common/Button';
const NAV: {
  path: string;
  key: string;
  icon: IconName;
}[] = [
    { path: '/', key: 'nav.home', icon: 'home' }, { path: '/map', key: 'nav.map', icon: 'map' },
    { path: '/advisory', key: 'nav.advisory', icon: 'heart' }, { path: '/community', key: 'nav.community', icon: 'users' },
    { path: '/dashboard', key: 'nav.dashboard', icon: 'chart' },
  ];
export default function Layout() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const { alerts, areas } = useApp();
  const [menu, setMenu] = useState(false);
  const [about, setAbout] = useState(false);
  const [notices, setNotices] = useState(false);
  const toast = useToast();
  const location = useLocation();
  const navigate = useNavigate();
  const main = useRef<HTMLElement>(null);
  const initial = useRef(true);
  useEffect(() => {
    setMenu(false);
    window.scrollTo({ top: 0, behavior: 'instant' });
    const title = NAV.find((item) => item.path === location.pathname)?.key;
    document.title = `${title ? t(title) : 'Aero Health'} | Aero Health`;
    if (!initial.current)
      main.current?.focus({ preventScroll: true });
    initial.current = false;
  }, [location.pathname, t]);
  const triggered = alerts.filter((alert) => alert.enabled && (areas.find((area) => area.id === alert.areaId)?.reading?.aqi ?? -1) >= alert.threshold);
  async function signOut() {
    try {
      await logout();
      toast(t('signedOut'));
      navigate('/');
    }
    catch (error) {
      toast(errorMessage(error), 'error');
    }
  }
  return <>
    <a className="skip-link" href="#main-content">{t('skipContent')}</a>
    <div className="app-frame">
      <header className="site-header">
        <Logo />
        <nav className="desktop-nav" aria-label="Main navigation">{NAV.map((item) => <NavLink key={item.path} to={item.path} end={item.path === '/'} className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}>
          <Icon name={item.icon} size={17} />
          {t(item.key)}
        </NavLink>)}</nav>
        <div className="header-actions">
          <button className="language-button" aria-label="Switch language" onClick={() => void i18n.changeLanguage(i18n.language === 'ne' ? 'en' : 'ne')}>
            <Icon name="globe" size={16} />
            <span>{i18n.language === 'ne' ? 'EN' : '\u0928\u0947'}</span>
          </button>
          <button className="icon-button notification-button" onClick={() => setNotices(true)} aria-label={t('activeAlerts')}>
            <Icon name="bell" size={20} />
            {triggered.length > 0 && <i />}
          </button>
          <Link to={user ? '/profile' : '/login'} className="profile-pill">
            <span className="avatar">{user ? user.name.charAt(0).toUpperCase() : <Icon name="user" size={17} />}</span>
            <span>{user ? user.name.split(' ')[0] : t('signIn')}</span>
            <Icon name="chevron-down" size={13} />
          </Link>
          <button className="icon-button mobile-menu-button" onClick={() => setMenu(!menu)} aria-expanded={menu} aria-controls="mobile-menu" aria-label="Navigation menu">
            <Icon name={menu ? 'close' : 'menu'} />
          </button>
        </div>
      </header>
      {menu && <nav className="mobile-nav" id="mobile-menu" aria-label="Mobile navigation">
        {NAV.map((item) => <NavLink key={item.path} to={item.path} end={item.path === '/'}>
          <Icon name={item.icon} size={18} />
          {t(item.key)}
        </NavLink>)}
        <Link to="/awareness">
          <Icon name="book" size={18} />
          {t('nav.awareness')}
        </Link>
        {user?.role === 'admin' && <Link to="/admin">
          <Icon name="shield" size={18} />
          {t('nav.admin')}
        </Link>}
        {user && <button onClick={signOut}>
          <Icon name="logout" size={18} />
          {t('signOut')}
        </button>}
      </nav>}
      <main id="main-content" ref={main} tabIndex={-1}>
        <Outlet />
      </main>
      <footer className="site-footer">
        <div>
          <Logo />
          <p>{t('footerTagline')}</p>
        </div>
        <div className="footer-links">
          <Link to="/awareness">{t('nav.awareness')}</Link>
          <Link to="/compare">{t('compareAreas')}</Link>
          <Link to="/design-system">{t('designSystem')}</Link>
          <button onClick={() => setAbout(true)}>{t('about')}</button>
          {user?.role === 'admin' && <Link to="/admin">{t('nav.admin')}</Link>}
          {user && <button onClick={signOut}>{t('signOut')}</button>}
        </div>
        <div className="footer-bottom">
          <span>{t(IS_DEMO ? 'footerDemo' : 'footerReal')}</span>
          <span>{t('allRights')}</span>
        </div>
      </footer>
    </div>
    <Modal title={t('about')} open={about} onClose={() => setAbout(false)}>
      <div className="modal-copy">
        <span className="demo-pill">
          <span />
          {t(IS_DEMO ? 'demoMode' : 'liveMode')}
        </span>
        <p>{t(IS_DEMO ? 'demoDetails' : 'backendNotice')}</p>
        <h3>{t('privacy')}</h3>
        <p>{t('demoPrivacy')}</p>
        <p className="disclaimer">
          <Icon name="info" size={16} />
          {t('medicalDisclaimer')}
        </p>
      </div>
    </Modal>
    <Modal title={t('activeAlerts')} open={notices} onClose={() => setNotices(false)}>
      <div className="modal-copy">
        <p className="notice">{t('alertDemoNotice')}</p>
        {!triggered.length ? <p>{t('noAlertsBody')}</p> : triggered.map((alert) => <div className="notification-row" key={alert.id}>
          <Icon name="bell" />
          <div>
            <strong>{areas.find((area) => area.id === alert.areaId)?.name}</strong>
            <p>{t('aboveThreshold')}: {alert.threshold} AQI</p>
          </div>
        </div>)}
        <ButtonLink to="/dashboard" onClick={() => setNotices(false)}>
          {t('manageAlerts')}
          <Icon name="arrow-right" size={16} />
        </ButtonLink>
      </div>
    </Modal>
  </>;
}
