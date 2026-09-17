import { useTranslation } from 'react-i18next';
import { useApp } from '../../context/AppContext';
export default function AreaSelect({ value, onChange, id = 'area-select', onlyReadings = false, label }: {
  value: string;
  onChange: (id: string) => void;
  id?: string;
  onlyReadings?: boolean;
  label?: string;
}) {
  const { areas } = useApp();
  const { t, i18n } = useTranslation();
  return <label className="field" htmlFor={id}>
    <span>{label || t('selectArea')}</span>
    <select id={id} value={value} onChange={(event) => onChange(event.target.value)}>{areas.filter((area) => !onlyReadings || area.reading).map((area) => <option key={area.id} value={area.id}>{i18n.language === 'ne' ? area.nameNe : area.name} - {t(`district.${area.district}`)}</option>)}</select>
  </label>;
}
