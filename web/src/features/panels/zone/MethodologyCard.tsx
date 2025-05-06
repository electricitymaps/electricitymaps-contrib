import Accordion from 'components/Accordion';
import Link from 'components/Link';
import { LogoIcon } from 'components/Logo';
import { DataSources } from 'features/charts/DataSources';
import useZoneDataSources from 'features/charts/hooks/useZoneDataSources';
import { RoundedCard } from 'features/charts/RoundedCard';
import { useEvents, useTrackEvent } from 'hooks/useTrackEvent';
import { t } from 'i18next';
import { Factory, UtilityPole, Zap } from 'lucide-react';
import { memo, useMemo, useState } from 'react';

function MethodologyCard() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const trackEvent = useTrackEvent();
  const {
    trackMissingDataMethodology,
    trackCarbonIntensityMethodology,
    trackDataCollectionMethodology,
    trackHistoricalAggregatesMethodology,
  } = useEvents(trackEvent);

  const {
    capacitySources,
    emissionFactorSources,
    powerGenerationSources,
    emissionFactorSourcesToProductionSources,
  } = useZoneDataSources();

  const methodologyAndDataSources = useMemo(
    () => ({
      missingData: {
        href: 'https://www.electricitymaps.com/methodology#missing-data',
        text: 'left-panel.applied-methodologies.estimations',
        onClick: () => trackMethodology('missing-data'),
      },
      dataCollectionAndProcessing: {
        href: 'https://www.electricitymaps.com/methodology#data-collection-and-processing',
        text: 'left-panel.applied-methodologies.flowtracing',
        onClick: trackDataCollectionMethodology,
      },
      carbonIntensityAndEmissionFactors: {
        href: 'https://www.electricitymaps.com/methodology#carbon-intensity-and-emission-factors',
        text: 'left-panel.applied-methodologies.carbonintensity',
        onClick: trackCarbonIntensityMethodology,
      },
      historicalAggregates: {
        href: 'https://github.com/electricityMaps/electricitymaps-contrib/wiki/Historical-aggregates',
        text: 'left-panel.applied-methodologies.historicalAggregations',
        onClick: trackHistoricalAggregatesMethodology,
      },
    }),
    [
      trackMissingDataMethodology,
      trackCarbonIntensityMethodology,
      trackDataCollectionMethodology,
      trackHistoricalAggregatesMethodology,
    ]
  );

  return (
    <RoundedCard>
      <Accordion
        title={t('left-panel.methodologies-and-data-sources.title')}
        className="text-md pt-2"
        isCollapsed={isCollapsed}
        setState={setIsCollapsed}
      >
        <div className="flex flex-col gap-2 py-1">
          <div className="flex items-center gap-1 py-2">
            <LogoIcon className="size-4 dark:text-white" />
            <p className="font-semibold">{t('left-panel.applied-methodologies.title')}</p>
          </div>
          <div className="flex flex-col gap-2 pl-5">
            {Object.entries(methodologyAndDataSources).map(
              ([key, { href, text, onClick }]) => (
                <Link key={key} href={href} onClick={onClick}>
                  {t(text)}
                </Link>
              )
            )}
          </div>

          <DataSources
            title={t('data-sources.capacity')}
            icon={<UtilityPole size={16} />}
            sources={capacitySources}
          />
          <DataSources
            title={t('data-sources.power')}
            icon={<Zap size={16} />}
            sources={powerGenerationSources}
          />
          <DataSources
            title={t('data-sources.emission')}
            icon={<Factory size={16} />}
            sources={emissionFactorSources}
            emissionFactorSourcesToProductionSources={
              emissionFactorSourcesToProductionSources
            }
          />
        </div>
      </Accordion>
    </RoundedCard>
  );
}

export default memo(MethodologyCard);
