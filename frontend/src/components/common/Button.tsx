import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { Link, type LinkProps } from 'react-router-dom';
export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'mint';
export default function Button({ children, variant = 'primary', loading = false, className = '', disabled, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  loading?: boolean;
  children: ReactNode;
}) {
  return <button type="button" className={`button button-${variant} ${className}`} disabled={disabled || loading} aria-busy={loading || undefined} {...props}>{loading && <span className="spinner spinner-small" aria-hidden="true" />}{children}</button>;
}
export function ButtonLink({ children, variant = 'primary', className = '', ...props }: LinkProps & {
  variant?: ButtonVariant;
}) {
  return <Link className={`button button-${variant} ${className}`} {...props}>{children}</Link>;
}
