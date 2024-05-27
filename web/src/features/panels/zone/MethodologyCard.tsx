import Accordion from 'components/Accordion';
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
        <div className="flex flex-col gap-2 pb-1 text-emerald-800 underline underline-offset-4 dark:text-emerald-500">
          <a
            href="https://www.electricitymaps.com/methodology#missing-data"
            target="_blank"
            rel="noreferrer"
            className={`text-sm font-semibold `}
          >
            <span>{t('left-panel.applied-methodologies.estimations')}</span>
          </a>
          <a
            href="https://www.electricitymaps.com/methodology#data-collection-and-processing"
            target="_blank"
            rel="noreferrer"
            className={`text-sm font-semibold `}
          >
            <span>{t('left-panel.applied-methodologies.flowtracing')}</span>
          </a>
          <a
            href="https://www.electricitymaps.com/methodology#carbon-intensity-and-emission-factors"
            target="_blank"
            rel="noreferrer"
            className={`text-sm font-semibold `}
          >
            <span>{t('left-panel.applied-methodologies.carbonintensity')}</span>
          </a>
        </div>
      </Accordion>
    </RoundedCard>
  );
}
