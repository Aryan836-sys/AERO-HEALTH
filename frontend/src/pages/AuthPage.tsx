import { useState, type FormEvent } from 'react';
import { Link, Navigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../context/ToastContext';
import { IS_DEMO } from '../services/api';
import { DEMO_CREDENTIALS } from '../services/mockApi';
import { errorMessage } from '../utils/format';
import { validEmail } from '../utils/validation';
import Icon from '../components/common/Icon';
import Button from '../components/common/Button';
import DemoBadge from '../components/common/DemoBadge';
import { LoadingState } from '../components/common/states';
export default function AuthPage({ register = false }: {
  register?: boolean;
}) {
  const { t } = useTranslation();
  const auth = useAuth();
  const toast = useToast();
  const [params] = useSearchParams();
  const requestedNext = params.get('next') ?? '/dashboard';
  const next = /^\/(?!\/)/.test(requestedNext) && !requestedNext.includes('\\') && !/^\/(login|register)(?:[/?#]|$)/.test(requestedNext) ? requestedNext : '/dashboard';
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  async function authenticate(event?: FormEvent, role?: 'user' | 'admin') {
    event?.preventDefault();
    setError('');
    const errors: Record<string, string> = {};
    if (!role) {
      if (register && name.trim().length < 2)
        errors.name = t('invalidName');
      if (!validEmail(email))
        errors.email = t('invalidEmail');
      if (register ? password.length < 8 : !password)
        errors.password = t(register ? 'invalidPassword' : 'loginPasswordRequired');
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length)
      return;
    setBusy(true);
    try {
      if (role) {
        await auth.login(DEMO_CREDENTIALS[role].email, DEMO_CREDENTIALS[role].password);
      }
      else if (register) {
        await auth.register(name, email, password);
      }
      else {
        await auth.login(email, password);
      }
      toast.success(t(register && !role ? 'registered' : 'welcomeBack'));
    }
    catch (failure) {
      setError(errorMessage(failure));
    }
    finally {
      setBusy(false);
    }
  }
  if (!auth.ready)
    return <LoadingState />;
  if (auth.user)
    return <Navigate to={next} replace />;
  return (<div className="page-content auth-page">
    <section className="auth-story">
      <span className="eyebrow">AERO HEALTH / YOUR EVERYDAY COMPANION</span>
      <h1>{t('login.title')}</h1>
      <p>{t('login.description')}</p>
      <div className="auth-orbits" aria-hidden="true">
        <div className="orbit-line orbit-one" />
        <div className="orbit-line orbit-two" />
        <div className="orbit-line orbit-three" />
        <span className="auth-orbit-center">
          <Icon name="wind" size={68} />
        </span>
        <span className="orbit-satellite satellite-leaf">
          <Icon name="leaf" size={26} />
        </span>
        <span className="orbit-satellite satellite-heart">
          <Icon name="heart" size={24} />
        </span>
        <span className="orbit-satellite satellite-map">
          <Icon name="pin" size={23} />
        </span>
      </div>
      <div className="auth-story-footer">
        <Icon name="shield" size={20} />
        <span>{t('profileOptional')}</span>
        <DemoBadge />
      </div>
    </section>
    <section className="auth-form-card">
      <span className="icon-disc lavender">
        <Icon name={register ? 'user' : 'lock'} size={24} />
      </span>
      <h2>{t(register ? 'createAccount' : 'signIn')}</h2>
      <p className="muted">{t('login.eyebrow')}</p>
      <form onSubmit={(event) => void authenticate(event)} noValidate className="form-stack">
        {register && <label className="field">
          {t('name')}
          <input name="name" autoComplete="name" maxLength={80} value={name} onChange={(event) => setName(event.target.value)} aria-invalid={!!fieldErrors.name} aria-describedby={fieldErrors.name ? 'name-error' : undefined} />
          {fieldErrors.name && <span id="name-error" className="field-error">{fieldErrors.name}</span>}
        </label>}
        <label className="field">
          {t('email')}
          <input name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} aria-invalid={!!fieldErrors.email} aria-describedby={fieldErrors.email ? 'email-error' : undefined} placeholder="you@example.com" />
          {fieldErrors.email && <span id="email-error" className="field-error">{fieldErrors.email}</span>}
        </label>
        <label className="field">
          {t('password')}
          <span className="password-field">
            <input name="password" type={showPassword ? 'text' : 'password'} autoComplete={register ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} aria-invalid={!!fieldErrors.password} aria-describedby="password-note" />
            <button className="icon-button" type="button" onClick={() => setShowPassword(!showPassword)} aria-label={t(showPassword ? 'hidePassword' : 'showPassword')}>
              <Icon name={showPassword ? 'eye-off' : 'eye'} size={18} />
            </button>
          </span>
          <span id="password-note" className={fieldErrors.password ? 'field-error' : 'field-help'}>{fieldErrors.password || (register ? t('passwordHint') : '')}</span>
        </label>
        {error && <div className="inline-error" role="alert">
          <Icon name="alert" />
          {error}
        </div>}
        <Button type="submit" loading={busy} className="full-width">
          {t(register ? 'createAccount' : 'signIn')}
          <Icon name="arrow-right" size={18} />
        </Button>
      </form>
      <p className="auth-switch">
        {t(register ? 'alreadyAccount' : 'noAccount')}
        {" "}
        <Link className="text-button" to={`${register ? '/login' : '/register'}?next=${encodeURIComponent(next)}`}>{t(register ? 'signIn' : 'createAccount')}</Link>
      </p>
      {IS_DEMO && <>
        <div className="divider-label">{t('demoAccounts')}</div>
        <div className="demo-auth-buttons">
          <Button variant="mint" disabled={busy} onClick={() => void authenticate(undefined, 'user')}>
            <Icon name="user" size={17} />
            {t('tryDemo')}
          </Button>
          <Button variant="secondary" disabled={busy} onClick={() => void authenticate(undefined, 'admin')}>
            <Icon name="shield" size={17} />
            {t('tryAdmin')}
          </Button>
        </div>
        <p className="privacy-note">
          <Icon name="info" size={16} />
          {t('demoPrivacy')}
        </p>
      </>}
    </section>
  </div>);
}
