import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { TimeAverages } from 'utils/constants';
import { timeAverageAtom } from 'utils/state/atoms';

export default function BySource({ className }: { className?: string }) {
  const { __ } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);

  return (
    <div className={`relative top-2 mb-1 text-sm ${className}`}>
      {__(
        timeAverage !== TimeAverages.HOURLY
          ? 'country-panel.averagebysource'
          : 'country-panel.bysource'
      )}
    </div>
  );
}
