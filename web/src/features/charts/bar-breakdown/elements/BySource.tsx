import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';

export default function BySource({ className }: { className?: string }) {
  const { __ } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  return (
    <div className={`relative pb-2 pt-4 text-md font-bold ${className}`}>
      {__(
        displayByEmissions
          ? 'country-panel.emissions'
          : 'country-panel.electricityproduction'
      )}{' '}
      {__(
        timeAverage === TimeAverages.HOURLY
          ? 'country-panel.bysource'
          : 'country-panel.averagebysource'
      )}
    </div>
  );
}
