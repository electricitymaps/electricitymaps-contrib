import { Clock } from 'lucide-react';
import { useTranslation } from 'react-i18next';

export function NewFeaturePopoverContent() {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col text-left">
      <div className="flex flex-row items-center gap-2">
        <Clock size={16} />
        <h3>{t(`new-feature-popover.title`)}</h3>
      </div>
      <p>{t(`new-feature-popover.content`)}</p>
    </div>
  );
}
