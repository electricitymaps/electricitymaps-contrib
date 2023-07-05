import CarbonIntensitySquare from 'components/CarbonIntensitySquare';
import { CircularGauge } from 'components/CircularGauge';
import { useAtom } from 'jotai';
import { useTranslation } from 'translation/translation';
import { Mode } from 'utils/constants';
import { getCarbonIntensity, getFossilFuelRatio, getRenewableRatio } from 'utils/helpers';
import { productionConsumptionAtom, selectedDatetimeIndexAtom } from 'utils/state/atoms';
import { ZoneDetails } from 'types';
import { HiExclamationTriangle } from 'react-icons/hi2';

function LowCarbonTooltip() {
  const { __ } = useTranslation();
  return (
    <div className="text-left">
      <b>{__('tooltips.lowcarbon')}</b>
      <br />
      <small>{__('tooltips.lowCarbDescription')}</small>
      <br />
    </div>
  );
}

function truncateString(string_: string, number_: number) {
  return string_.length <= number_ ? string_ : string_.slice(0, number_) + '...';
}

function OutageMessage({
  outageData: outageData,
}: {
  outageData: ZoneDetails['zoneMessage'];
}) {
  if (!outageData || !outageData.message) {
    return null;
  }
  return (
    <div className="overflow-hidden px-2 text-gray-800 sm:pl-4">
      <div className="flex w-full  items-center rounded-lg border border-yellow-300 bg-yellow-100 p-2 text-sm">
        <div>
          <HiExclamationTriangle className="mr-2 text-yellow-600" size="20" />
        </div>
        <span className="inline overflow-hidden">
          {truncateString(outageData.message, 300)}{' '}
          {outageData?.issue && outageData.issue != 'None' && (
            <span className="inline-flex">
              - see{' '}
              <a
                className="inline-flex"
                href={`https://github.com/electricitymaps/electricitymaps-contrib/issues/${outageData.issue}`}
              >
                <span className="pl-1 text-blue-600 underline">
                  issue #{outageData.issue}
                </span>
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  className="ml-1"
                >
                  <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                </svg>
              </a>
            </span>
          )}
        </span>
      </div>
    </div>
  );
}

export function ZoneHeaderGauges({ data }: { data?: ZoneDetails }) {
  const { __ } = useTranslation();
  const [currentMode] = useAtom(productionConsumptionAtom);
  const [selectedDatetime] = useAtom(selectedDatetimeIndexAtom);
  const isConsumption = currentMode === Mode.CONSUMPTION;
  const selectedData = data?.zoneStates[selectedDatetime.datetimeString];

  const {
    co2intensity,
    renewableRatio,
    fossilFuelRatio,
    co2intensityProduction,
    renewableRatioProduction,
    fossilFuelRatioProduction,
  } = selectedData || {};

  const intensity = getCarbonIntensity(
    isConsumption,
    co2intensity,
    co2intensityProduction
  );
  const renewable = getRenewableRatio(
    isConsumption,
    renewableRatio,
    renewableRatioProduction
  );
  const fossilFuelPercentage = getFossilFuelRatio(
    isConsumption,
    fossilFuelRatio,
    fossilFuelRatioProduction
  );
  const outageData = data?.zoneMessage;

  return (
    <div className="mt-1 grid w-full gap-y-5 sm:pr-4">
      {outageData && <OutageMessage outageData={outageData} />}

      <div className="flex flex-row justify-evenly">
        <CarbonIntensitySquare
          data-test-id="co2-square-value"
          intensity={intensity}
          withSubtext
        />
        <CircularGauge
          name={__('country-panel.lowcarbon')}
          ratio={fossilFuelPercentage}
          tooltipContent={<LowCarbonTooltip />}
          testId="zone-header-lowcarbon-gauge"
        />
        <CircularGauge
          name={__('country-panel.renewable')}
          ratio={renewable}
          testId="zone-header-renewable-gauge"
        />
      </div>
    </div>
  );
}
