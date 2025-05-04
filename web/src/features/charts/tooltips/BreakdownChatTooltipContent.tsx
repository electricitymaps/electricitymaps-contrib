import { CarbonIntensityDisplay } from 'components/CarbonIntensityDisplay';
import { CountryFlag } from 'components/Flag';
import { MetricRatio } from 'components/MetricRatio';
import { TFunction } from 'i18next';
import { useAtomValue } from 'jotai';
import { InfoIcon } from 'lucide-react';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { getZoneName } from 'translation/translation';
import { Maybe } from 'types';
import { formatCo2, formatEnergy, formatPower } from 'utils/formatting';
import { isHourlyAtom } from 'utils/state/atoms';

import { getRatioPercent } from '../graphUtils';
import { LayerKey } from '../types';

function Headline({
  isExchange,
  displayByEmissions,
  zoneKey,
  selectedLayerKey,
  percentageUsage,
  t,
  isExport,
}: {
  isExchange: boolean;
  displayByEmissions: boolean;
  zoneKey: string;
  selectedLayerKey: LayerKey;
  percentageUsage: string;
  t: TFunction;
  isExport: boolean;
}) {
  const availabilityKey = displayByEmissions
    ? 'emissionsAvailableIn'
    : 'electricityAvailableIn';

  const dataActionKey = getDataActionKey(isExchange, isExport, displayByEmissions);

  return (
    <div>
      <b>{percentageUsage} %</b> {t(availabilityKey)}
      <span className="mx-1 inline-flex">
        <CountryFlag className="shadow-3xl" zoneId={zoneKey} />
      </span>
      <b>{getZoneName(zoneKey)}</b> {t(dataActionKey)}
      {!isExchange && ` ${t(selectedLayerKey)}`}
      {isExchange && (
        <>
          <span className="mx-1 inline-flex">
            <CountryFlag className="shadow-3xl" zoneId={selectedLayerKey} />
          </span>
          <b>{getZoneName(selectedLayerKey)}</b>
        </>
      )}
    </div>
  );
}

function getDataActionKey(
  isExchange: boolean,
  isExport: boolean,
  displayByEmissions: boolean
) {
  if (isExchange) {
    if (isExport) {
      return displayByEmissions ? 'emissionsExportedTo' : 'electricityExportedTo';
    }
    return displayByEmissions ? 'emissionsImportedFrom' : 'electricityImportedFrom';
  } else {
    if (isExport) {
      return displayByEmissions ? 'emissionsStoredUsing' : 'electricityStoredUsing';
    }
    return 'comesFrom';
  }
}

interface BreakdownChartTooltipContentProperties {
  usage: number | null;
  capacity: number | null | undefined;
  totalElectricity: number;
  totalEmissions: number;
  co2Intensity?: number;
  displayByEmissions: boolean;
  emissions: number;
  zoneKey: string;
  isExchange: boolean;
  isExport: boolean;
  selectedLayerKey: LayerKey;
  co2IntensitySource?: string;
  storage?: Maybe<number>;
  production?: Maybe<number>;
  capacitySource?: string[] | null;
}

export function BreakdownChartTooltipContent({
  usage,
  totalElectricity,
  displayByEmissions,
  capacity,
  emissions,
  isExport,
  totalEmissions,
  co2Intensity,
  co2IntensitySource,
  zoneKey,
  isExchange,
  selectedLayerKey,
  capacitySource,
}: BreakdownChartTooltipContentProperties) {
  const { t } = useTranslation();

  const isHourly = useAtomValue(isHourlyAtom);
  // Dynamically generate the translated headline HTML based on the exchange or generation type
  const percentageUsage = displayByEmissions
    ? getRatioPercent(emissions, totalEmissions)
    : getRatioPercent(usage, totalElectricity);

  return (
    <>
      <Headline
        isExchange={isExchange}
        displayByEmissions={displayByEmissions}
        percentageUsage={percentageUsage.toString()}
        zoneKey={zoneKey}
        selectedLayerKey={selectedLayerKey}
        t={t}
        isExport={isExport}
      />
      {displayByEmissions && (
        <MetricRatio
          value={emissions}
          total={totalEmissions}
          format={formatCo2}
          label={t('ofCO2eq')}
          useTotalUnit
        />
      )}

      {!displayByEmissions && (
        // Used to prevent browser translation crashes on edge, see #6809
        <div translate="no">
          <MetricRatio
            value={usage}
            total={totalElectricity}
            useTotalUnit
            format={isHourly ? formatPower : formatEnergy}
          />
          <br />
          {isHourly && (
            <>
              <br />
              {t('tooltips.utilizing')} <b>{getRatioPercent(usage, capacity)} %</b>{' '}
              {t('tooltips.ofinstalled')}
              <br />
              <MetricRatio
                value={usage}
                total={capacity}
                useTotalUnit
                format={formatPower}
              />
              {capacitySource && (
                <small>
                  {' '}
                  ({t('country-panel.source')}: {capacitySource})
                </small>
              )}
              <br />
            </>
          )}
          <br />
          {t('tooltips.representing')}{' '}
          <b>{getRatioPercent(emissions, totalEmissions)} %</b>{' '}
          {t('tooltips.ofemissions')}
          <br />
          <MetricRatio
            value={emissions}
            total={totalEmissions}
            format={formatCo2}
            label={t('ofCO2eq')}
            useTotalUnit
          />
        </div>
      )}
      {!displayByEmissions && (Number.isFinite(co2Intensity) || usage !== 0) && (
        <>
          <br />
          {t('tooltips.withcarbonintensity')}
          <br />
          <div className="flex-wrap">
            <div className="inline-flex items-center gap-x-1">
              <CarbonIntensityDisplay withSquare co2Intensity={co2Intensity} />
            </div>
            {!isExchange && (
              <small>
                {' '}
                ({t('country-panel.source')}: {co2IntensitySource || '?'})
              </small>
            )}
          </div>
        </>
      )}
    </>
  );
}

export const BreakdownChartTooltipContentNoData = memo(
  function BreakdownChartTooltipContentNoData({ isExchange }: { isExchange: boolean }) {
    const { t } = useTranslation();

    return (
      <div className="row flex items-center gap-1 rounded-lg bg-elevation p-2 dark:bg-elevation-dark">
        <InfoIcon size={16} />
        {t(isExchange ? 'tooltips.noDataExchange' : 'tooltips.noDataProduction')}
      </div>
    );
  }
);
