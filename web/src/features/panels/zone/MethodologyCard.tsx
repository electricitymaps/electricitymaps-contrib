import Accordion from 'components/Accordion';
import Link from 'components/Link';
import { LogoIcon } from 'components/Logo';
import { DataSources } from 'features/charts/DataSources';
import useZoneDataSources from 'features/charts/hooks/useZoneDataSources';
import { RoundedCard } from 'features/charts/RoundedCard';
import { t } from 'i18next';
import { Factory, UtilityPole, Zap } from 'lucide-react';
import { usePostHog } from 'posthog-js/react';
import { memo, useState } from 'react';
import { trackEvent } from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

const methodologyAndDataSources = {
  missingData: {
    href: 'https://www.electricitymaps.com/methodology#missing-data',
    text: t('left-panel.applied-methodologies.estimations'),
    link: 'missing-data',
  },
  dataCollectionAndProcessing: {
    href: 'https://www.electricitymaps.com/methodology#data-collection-and-processing',
    text: t('left-panel.applied-methodologies.flowtracing'),
    link: 'data-collection-and-processing-data',
  },
  carbonIntensityAndEmissionFactors: {
    href: 'https://www.electricitymaps.com/methodology#carbon-intensity-and-emission-factors',
    text: t('left-panel.applied-methodologies.carbonintensity'),
    link: 'carbon-intensity-and-emission-factors',
  },
  historicalAggregates: {
    href: 'https://github.com/electricityMaps/electricitymaps-contrib/wiki/Historical-aggregates',
    text: t('left-panel.applied-methodologies.historicalAggregations'),
    link: 'historical-aggregates',
  },
};

function MethodologyCard() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  const posthog = usePostHog();
  const {
    capacitySources,
    emissionFactorSources,
    powerGenerationSources,
    emissionFactorSourcesToProductionSources,
  } = useZoneDataSources();

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
              ([key, { href, text, link }]) => (
                <Link
                  key={key}
                  href={href}
                  onClick={() =>
                    trackEvent(posthog, TrackEvent.MAP_METHODOLOGY_LINK_VISITED, { link })
                  }
                >
                  {text}
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
