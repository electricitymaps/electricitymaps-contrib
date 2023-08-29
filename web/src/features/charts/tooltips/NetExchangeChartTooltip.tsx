import { useAtom } from 'jotai';
import { getZoneName, useTranslation } from 'translation/translation';
import { displayByEmissionsAtom, timeAverageAtom } from 'utils/state/atoms';
import { InnerAreaGraphTooltipProps } from '../types';
import AreaGraphToolTipHeader from './AreaGraphTooltipHeader';
import {
  getNetConsumption,
  getNetExchange,
  getNetProduction,
  round,
} from 'utils/helpers';
import { scalePower } from 'utils/formatting';
import { getRatioPercent } from '../graphUtils';
import { CountryFlag } from 'components/Flag';

export default function NetExchangeChartTooltip({
  zoneDetail,
}: InnerAreaGraphTooltipProps) {
  if (!zoneDetail) {
    return null;
  }
  const [timeAverage] = useAtom(timeAverageAtom);
  const [displayByEmissions] = useAtom(displayByEmissionsAtom);
  const { __ } = useTranslation();

  const { stateDatetime } = zoneDetail;

  const netExchange = getNetExchange(zoneDetail, displayByEmissions);
  const netProduction = getNetProduction(zoneDetail, displayByEmissions);
  const netConsumption = getNetConsumption(zoneDetail, displayByEmissions);
  const zoneKey = zoneDetail.zoneKey;
  const { formattingFactor, unit } = displayByEmissions
    ? {
        formattingFactor: 1,
        unit: 'tCO₂eq / min',
      }
    : scalePower(netExchange);

  return (
    <div className="w-full rounded-md bg-white p-3 shadow-xl dark:bg-gray-900 sm:w-max">
      <AreaGraphToolTipHeader
        datetime={new Date(stateDatetime)}
        timeAverage={timeAverage}
        squareColor="#7f7f7f"
        title={__('tooltips.netExchange')}
      />
      <p className="flex justify-center text-base">
        {netExchange >= 0 ? __('tooltips.importing') : __('tooltips.exporting')}{' '}
        <b className="mx-1">{Math.abs(round(netExchange / formattingFactor))}</b> {unit}
      </p>
      <p className="inline-flex flex-wrap items-center justify-center gap-x-1 text-sm">
        {__('tooltips.representing')} {}
        <b>
          {getRatioPercent(
            Math.abs(netExchange),
            netExchange >= 0 ? netConsumption : netProduction
          )}{' '}
          %
        </b>
        of {displayByEmissions ? 'carbon emissions' : 'electricity'}{' '}
        {netExchange >= 0 ? 'consumed' : 'produced'} in{' '}
        {<CountryFlag className="shadow-3xl" zoneId={zoneKey} />}{' '}
        <b> {getZoneName(zoneKey)} </b>
      </p>
    </div>
  );
}
