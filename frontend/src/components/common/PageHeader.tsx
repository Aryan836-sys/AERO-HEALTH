import type { ReactNode } from 'react';
export default function PageHeader({ eyebrow, title, description, action }: {
  eyebrow: string;
  title: ReactNode;
  description?: string;
  action?: ReactNode;
}) {
  return <div className="page-header">
    <div>
      <p className="eyebrow">
        <span />
        {eyebrow}
      </p>
      <h1>{title}</h1>
      {description && <p className="page-description">{description}</p>}
    </div>
    {action && <div className="page-header-actions">{action}</div>}
  </div>;
}
