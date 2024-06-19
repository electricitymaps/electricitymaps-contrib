import Accordion from 'components/Accordion';
import InfoText from 'features/modals/InfoText';
import { useTranslation } from 'react-i18next';
import { rankingPanelAccordionCollapsedAtom } from 'utils/state/atoms';

export default function RankingPanelAccordion() {
  const { t } = useTranslation();
  return (
    <Accordion
      title={t('info.title')}
      className="py-1"
      isCollapsedAtom={rankingPanelAccordionCollapsedAtom}
      isOnTop
    >
      <InfoText />
    </Accordion>
  );
}
