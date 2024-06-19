import Accordion from 'components/Accordion';
import { useTranslation } from 'react-i18next';
import { rankingPanelAccordionCollapsedAtom } from 'utils/state/atoms';

export default function RankingPanelAccordion() {
  const { t } = useTranslation();
  return (
    <Accordion
      title={t('ranking-panel.accordion.title')}
      isCollapsedAtom={rankingPanelAccordionCollapsedAtom}
    >
      <p>{t('ranking-panel.accordion.text')}</p>
    </Accordion>
  );
}
