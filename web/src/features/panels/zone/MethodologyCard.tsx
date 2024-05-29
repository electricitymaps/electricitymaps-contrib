import Accordion from 'components/Accordion';
import { Link } from 'components/Link';
import { RoundedCard } from 'features/charts/bar-breakdown/RoundedCard';
import { t } from 'i18next';
import { EmapsIcon } from 'icons/emapsIcon';
import trackEvent from 'utils/analytics';

export default function MethodologyCard() {
  return (
    <RoundedCard>
      <Accordion
        icon={<EmapsIcon />}
        title={t('left-panel.applied-methodologies.title')}
        className="pb-1 pt-3 text-md"
        onOpen={() => trackEvent('AppliedMethodologies Expanded')}
      >
        <div className="flex flex-col gap-2 pb-1 ">
          <Link
            href="https://www.electricitymaps.com/methodology#missing-data"
            linkText={t('left-panel.applied-methodologies.estimations')}
          />
          <Link
            href="https://www.electricitymaps.com/methodology#data-collection-and-processing"
            linkText={t('left-panel.applied-methodologies.flowtracing')}
          />
          <Link
            href="https://www.electricitymaps.com/methodology#carbon-intensity-and-emission-factors"
            linkText={t('left-panel.applied-methodologies.carbonintensity')}
          />
        </div>
      </Accordion>
    </RoundedCard>
  );
}
