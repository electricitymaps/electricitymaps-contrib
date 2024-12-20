import Accordion from 'components/Accordion';
import { Link } from 'components/Link';
import InfoText from 'features/modals/InfoText';
import { useAtom } from 'jotai';
import { Trans, useTranslation } from 'react-i18next';
import { rankingPanelAccordionCollapsedAtom } from 'utils/state/atoms';

export default function RankingPanelAccordion() {
  const { t } = useTranslation();
  const [rankingPanelAccordionCollapsed, setRankingPanelAccordionCollapsed] = useAtom(
    rankingPanelAccordionCollapsedAtom
  );
  return (
    <Accordion
      title={t('info.title')}
      isTopExpanding
      isCollapsed={rankingPanelAccordionCollapsed}
      setState={setRankingPanelAccordionCollapsed}
    >
      <InfoText />
    </Accordion>
  );
}
