import Accordion from 'components/Accordion';
import { Link } from 'components/Link';
import { RoundedCard } from 'features/charts/RoundedCard';
import { t } from 'i18next';
import { EmapsIcon } from 'icons/emapsIcon';
import { useState } from 'react';
import trackEvent from 'utils/analytics';
import { TrackEvent } from 'utils/constants';

export default function MethodologyCard() {
  const [isCollapsed, setIsCollapsed] = useState(true);
  return (
    <RoundedCard>
      <Accordion
        icon={<EmapsIcon styling="dark:text-white" />}
        title={t('left-panel.applied-methodologies.title')}
        className="text-md pt-2"
        onOpen={() => trackEvent(TrackEvent.APPLIED_METHODOLOGIES_EXPANDED)}
        isCollapsed={isCollapsed}
        setState={setIsCollapsed}
      >
        <div className="flex flex-col gap-2 py-1">
          <Link href="https://www.electricitymaps.com/methodology#missing-data">
            {t('left-panel.applied-methodologies.estimations')}
          </Link>
          <Link href="https://www.electricitymaps.com/methodology#data-collection-and-processing">
            {t('left-panel.applied-methodologies.flowtracing')}
          </Link>
          <Link href="https://www.electricitymaps.com/methodology#carbon-intensity-and-emission-factors">
            {t('left-panel.applied-methodologies.carbonintensity')}
          </Link>
        </div>
      </Accordion>
    </RoundedCard>
  );
}
