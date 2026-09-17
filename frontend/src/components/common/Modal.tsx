import { useEffect, useId, useRef, type ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import Icon from './Icon';
export default function Modal({ open, title, children, onClose, wide = false }: {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();
  const { t } = useTranslation();
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog)
      return;
    if (!open) {
      if (dialog.open)
        dialog.close();
      return;
    }
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    dialog.showModal();
    const priorOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      if (dialog.open)
        dialog.close();
      document.body.style.overflow = priorOverflow;
      previous?.focus();
    };
  }, [open]);
  return <dialog ref={ref} className={`modal ${wide ? 'modal-wide' : ''}`} aria-labelledby={id} onCancel={(event) => { event.preventDefault(); onClose(); }} onClick={(event) => {
    if (event.target === event.currentTarget)
      onClose();
  }}>
    <div className="modal-inner">
      <div className="section-heading">
        <h2 id={id}>{title}</h2>
        <button className="icon-button" type="button" onClick={onClose} aria-label={t('close')}>
          <Icon name="close" />
        </button>
      </div>
      {open && children}
    </div>
  </dialog>;
}
