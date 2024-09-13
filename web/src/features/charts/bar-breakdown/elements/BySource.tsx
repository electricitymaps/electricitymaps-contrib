import EstimationBadge from 'components/EstimationBadge';
import { CountryFlag } from 'components/Flag';
import { Link } from 'components/Link';
import { TimeDisplay } from 'components/TimeDisplay';
import Logo from 'features/header/Logo';
import { useGetEstimationTranslation } from 'hooks/getEstimationTranslation';
import { TFunction } from 'i18next';
import { useAtom } from 'jotai';
import { CircleDashed, TrendingUpDown } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useParams } from 'react-router-dom';
import { getFullZoneName } from 'translation/translation';
import { EstimationMethods, TimeAverages } from 'utils/constants';
import {
  displayByEmissionsAtom,
  isTakingScreenshotAtom,
  productionConsumptionAtom,
  timeAverageAtom,
} from 'utils/state/atoms';

const getText = (
  timePeriod: TimeAverages,
  dataType: 'emissions' | 'production' | 'consumption',
  t: TFunction
) => {
  const translations = {
    hourly: {
      emissions: t('country-panel.by-source.emissions'),
      production: t('country-panel.by-source.electricity-production'),
      consumption: t('country-panel.by-source.electricity-consumption'),
    },
    default: {
      emissions: t('country-panel.by-source.total-emissions'),
      production: t('country-panel.by-source.total-electricity-production'),
      consumption: t('country-panel.by-source.total-electricity-consumption'),
    },
  };
  const period = timePeriod === TimeAverages.HOURLY ? 'hourly' : 'default';
  return translations[period][dataType];
};

export default function BySource({
  className,
  hasEstimationPill = false,
  estimatedPercentage,
  unit,
  estimationMethod,
}: {
  className?: string;
  hasEstimationPill?: boolean;
  estimatedPercentage?: number;
  unit?: string | number;
  estimationMethod?: EstimationMethods;
}) {
  const { t } = useTranslation();
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const [mixMode] = useAtom(productionConsumptionAtom);

  const dataType = displayByEmissions ? 'emissions' : mixMode;
  const text = getText(timeAverage, dataType, t);
  const pillText = useGetEstimationTranslation(
    'pill',
    estimationMethod,
    estimatedPercentage
  );
  const { zoneId } = useParams();
  const zoneNameFull = zoneId ? getFullZoneName(zoneId) : null;
  const [isTakingScreenShot, setIsTakingScreenshot] = useAtom(isTakingScreenshotAtom);
  return (
    <div className=" pt-2">
      {zoneId && isTakingScreenShot && (
        <>
          <div className="grid grid-cols-[auto_1fr_auto] items-center gap-2">
            <CountryFlag
              zoneId={zoneId}
              size={24}
              className="shadow-[0_0px_3px_rgba(0,0,0,0.2)]"
            />
            <h1 className="mb-5 ">{zoneNameFull}</h1>
            <Logo className="h-10 w-48 fill-black" />
          </div>

          <Link href="app.electricitymaps.com">app.electricitymaps.com</Link>
        </>
      )}
      <div
        className={`text-md relative flex flex-row justify-between font-bold ${className}`}
      >
        <div className="flex gap-1">
          <h2>{text}</h2>
        </div>
        {hasEstimationPill && (
          <EstimationBadge
            text={pillText}
            Icon={
              estimationMethod === EstimationMethods.TSA ? CircleDashed : TrendingUpDown
            }
          />
        )}
      </div>
      <TimeDisplay className="whitespace-nowrap text-sm" />
      {unit && <p className="dark:text-gray-300">{unit}</p>}
    </div>
  );
}
