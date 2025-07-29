import { RoundedCard } from 'features/charts/RoundedCard';
import { FlaskConicalIcon } from 'lucide-react';
import { memo, useCallback } from 'react';
import { useTranslation } from 'react-i18next';

export interface ExperimentalCardProps {
  title: string;
  description?: string;
}

function ExperimentalCard({ title, description }: ExperimentalCardProps) {
  const { t } = useTranslation();
  const supportsIntercom = typeof window !== 'undefined' && Boolean(window.Intercom);
  const handleChat = useCallback(() => {
    if (window.Intercom) {
      window.Intercom('show');
    } else {
      console.warn('Intercom not available');
    }
  }, []);
  return (
    <RoundedCard className="gap-2 border border-info-subtle bg-info-muted px-4 pb-2 pt-4 dark:border-info-subtle-dark dark:bg-info-muted-dark">
      <div className="flex items-center gap-2">
        <FlaskConicalIcon size={16} className="text-info-base dark:text-info-base-dark" />
        <h2 className="text-info-base dark:text-info-base-dark">{title}</h2>
      </div>
      {description && (
        <p className="text-info-base dark:text-info-base-dark">{description}</p>
      )}
      {/* This is hardcoded to use the Intercom chat for feedback, might be a good idea to allow a action to be passed as a prop if we are to reuse this for other things. */}
      {supportsIntercom && (
        <button
          className="text-sm font-semibold text-info-base underline dark:text-info-base-dark"
          onClick={handleChat}
        >
          {t('experiment.feedbackCta')}
        </button>
      )}
    </RoundedCard>
  );
}

export default memo(ExperimentalCard);
