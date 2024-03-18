import { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import { RoundedButton } from './RoundedButton';

interface Properties {
  showReloadButton?: boolean;
}

export default function LoadingSpinner({
  showReloadButton = false,
}: Properties): ReactElement {
  const { t } = useTranslation();
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="h-40 w-40 bg-[url('/images/loading-icon.svg')] bg-[length:100px] bg-center bg-no-repeat dark:bg-gray-900 dark:bg-[url('/images/loading-icon-darkmode.svg')]" />

      {showReloadButton && (
        <>
          <p>{t('misc.slow-loading-text')}</p>
          <RoundedButton
            size="lg"
            type="secondary"
            aria-label="Reload page"
            onClick={() => window.location.reload()}
          >
            {t('misc.reload')}
          </RoundedButton>
        </>
      )}
    </div>
  );
}
