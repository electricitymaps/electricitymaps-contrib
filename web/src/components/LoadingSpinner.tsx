import { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';

import { Button } from './Button';

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
          <Button
            size="lg"
            type="secondary-elevated"
            aria-label="Reload page"
            backgroundClasses="min-w-[330px] my-2"
            onClick={() => window.location.reload()}
          >
            {t('misc.reload')}
          </Button>
        </>
      )}
    </div>
  );
}
