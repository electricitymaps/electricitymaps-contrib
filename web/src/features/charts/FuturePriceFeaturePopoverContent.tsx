import { atomWithStorage } from 'jotai/utils';
import { useTranslation } from 'react-i18next';

export const newFuturePriceDismissed = atomWithStorage(
  'newFuturePriceDismissed',
  Boolean(localStorage.getItem('newFuturePriceDismissed') ?? true) ?? false
);

// TODO(cady): confirm copy & add translation strings
export function FuturePriceFeaturePopoverContent() {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col text-left">
      <div className="flex flex-row items-center gap-2">
        <h3>{'New! Future prices'}</h3>
      </div>
      <p>{'See the future prices for this zone'}</p>
    </div>
  );
}
