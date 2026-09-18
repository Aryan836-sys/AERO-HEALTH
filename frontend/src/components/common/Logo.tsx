import { Link } from 'react-router-dom';
export default function Logo({ light = false }: {
  light?: boolean;
}) {
  return <Link to="/" className={`logo ${light ? 'logo-light' : ''}`} aria-label="Aero Health home">
    <span className="logo-mark">
      <svg viewBox="0 0 44 44" fill="none" aria-hidden="true">
        <path d="m10 31 10-21c.8-1.6 2.4-1.6 3.2 0L34 31M15 24h14" stroke="currentColor" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M23 32h13" stroke="#79e3c8" strokeWidth="3.2" strokeLinecap="round" />
      </svg>
    </span>
    <span className="logo-word">aero<span>health</span><small>EVERY BREATH MATTERS</small></span>
  </Link>;
}
