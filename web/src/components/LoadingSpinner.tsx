import { LoadingSpinnerIcon } from 'icons/loadingSpinnerIcon';
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
      <div className={`flex max-h-[100px] max-w-[100px] items-center justify-center`}>
        <LoadingSpinnerIcon />
      </div>
      {showReloadButton && (
        <>
          <p>{t('misc.slow-loading-text')}</p>
          <Button
            size="lg"
            type="secondary"
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
