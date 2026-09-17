import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useToast } from '../context/ToastContext';
import { AQI_CATEGORIES } from '../utils/aqi';
import { readStored, writeStored } from '../services/storage';
import PageHeader from '../components/common/PageHeader';
import AqiIndicator from '../components/common/AqiIndicator';
import AqiGauge from '../components/common/AqiGauge';
import ReliabilityBadge from '../components/common/ReliabilityBadge';
import Button from '../components/common/Button';
import Icon from '../components/common/Icon';
import Modal from '../components/common/Modal';
import { EmptyState, ErrorState, LoadingState } from '../components/common/states';
export default function DesignSystem() {
  const { t } = useTranslation();
  const toast = useToast();
  const [contrast, setContrast] = useState(readStored('contrast', false));
  const [modal, setModal] = useState(false);
  function toggleContrast() {
    const next = !contrast;
    setContrast(next);
    writeStored('contrast', next);
    document.documentElement.classList.toggle('high-contrast', next);
    toast(t(next ? 'contrastOn' : 'contrastOff'));
  }
  return <div className="page-content">
    <PageHeader eyebrow={t('design.eyebrow')} title={t('design.title')} description={t('design.description')} action={<Button variant="secondary" onClick={toggleContrast}>
      <Icon name="eye" size={17} />
      {t(contrast ? 'defaultContrast' : 'contrast')}
    </Button>} />
    <section className="card">
      <div className="section-heading">
        <h2>{t('aqiScale')}</h2>
        <span className="subtle-pill">COLOR + LABEL + SYMBOL</span>
      </div>
      <p className="small muted">{t('designNote')}</p>
      <div className="design-aqi-grid">{AQI_CATEGORIES.map((category) => <section key={category.key}>
        <AqiGauge value={category.min} />
        <code>{category.color}</code>
        <AqiIndicator value={category.min} compact />
      </section>)}</div>
      <AqiIndicator value={null} />
    </section>
    <div className="design-two-column">
      <section className="card">
        <h2>{t('buttons')}</h2>
        <div className="button-demo-row">
          <Button onClick={() => toast(t('demoAction'))}>{t('primaryAction')}</Button>
          <Button variant="secondary" onClick={() => setModal(true)}>{t('openDialog')}</Button>
          <Button variant="mint" onClick={() => toast(t('demoAction'))}>
            <Icon name="check" size={16} />
            {t('save')}
          </Button>
          <Button disabled>{t('disabled')}</Button>
          <Button loading>{t('loading')}</Button>
        </div>
      </section>
      <section className="card">
        <h2>{t('dataReliability')}</h2>
        <div className="badge-demo-row">{(['official', 'community', 'modelled'] as const).map((reliability) => <ReliabilityBadge key={reliability} reliability={reliability} isDemo />)}</div>
      </section>
    </div>
    <h2 className="spaced-heading">{t('states')}</h2>
    <div className="design-state-grid">
      <section className="card">
        <LoadingState />
      </section>
      <section className="card">
        <EmptyState title={t('missingExample')} description={t('missingExampleBody')} />
      </section>
      <section className="card">
        <ErrorState message={t('testError')} onRetry={() => toast(t('demoAction'), 'info')} />
      </section>
    </div>
    <Modal open={modal} title={t('openDialog')} onClose={() => setModal(false)}>
      <p>{t('dialogDemoBody')}</p>
      <Button onClick={() => setModal(false)}>{t('close')}</Button>
    </Modal>
  </div>;
}
