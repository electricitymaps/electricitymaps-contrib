import Accordion from 'components/Accordion';
import { Link } from 'components/Link';
import { RoundedCard } from 'features/charts/RoundedCard';
import { t } from 'i18next';
import { EmapsIcon } from 'icons/emapsIcon';
import { atom } from 'jotai';
import trackEvent from 'utils/analytics';

const methodologyCardCollapsedAtom = atom<boolean | null>(null);

export default function MethodologyCard() {
  return (
    <RoundedCard>
      <Accordion
        icon={<EmapsIcon />}
        title={t('left-panel.applied-methodologies.title')}
        className="text-md pt-2"
        onOpen={() => trackEvent('AppliedMethodologies Expanded')}
        isCollapsedAtom={methodologyCardCollapsedAtom}
      >
        <div className="flex flex-col gap-2 py-1 ">
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
