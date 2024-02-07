import { ReactElement } from 'react';
import { useTranslation } from 'translation/translation';

import { Button } from './Button';

interface Properties {
  showReloadButton: boolean;
}

export default function LoadingSpinner({
  showReloadButton = false,
}: Properties): ReactElement {
  const { __ } = useTranslation();
  return (
    <div className="flex h-full flex-col items-center justify-center">
      <div className="h-40 w-40 bg-[url('/images/loading-icon.svg')] bg-[length:100px] bg-center bg-no-repeat dark:bg-gray-900 dark:bg-[url('/images/loading-icon-darkmode.svg')]" />

      {showReloadButton && (
        <>
          <p>{__('misc.slow-loading-text')}</p>
          <Button
            className="w-20 min-w-min dark:bg-gray-800/80"
            aria-label="Reload page"
            onClick={() => window.location.reload()}
          >
            {__('misc.reload')}
          </Button>
        </>
      )}
    </div>
  );
}
