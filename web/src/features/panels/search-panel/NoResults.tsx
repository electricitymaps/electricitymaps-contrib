import { useTranslation } from 'react-i18next';

export default function NoResults() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center gap-2 pb-6 pt-6">
      <p className="text-center text-sm text-neutral-500">
        {t('ranking-panel.no-results')}
      </p>
    </div>
  );
}
