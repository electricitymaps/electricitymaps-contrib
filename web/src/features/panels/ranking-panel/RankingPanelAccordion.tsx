import Accordion from 'components/Accordion';
import { ApiButton } from 'components/buttons/ApiButton';
import { DocumentationButton } from 'components/buttons/DocumentationButton';
import InfoText from 'features/modals/InfoText';
import { useAtom } from 'jotai';
import { useTranslation } from 'react-i18next';
import { rankingPanelAccordionCollapsedAtom } from 'utils/state/atoms';

export default function RankingPanelAccordion() {
  const { t } = useTranslation();
  const [rankingPanelAccordionCollapsed, setRankingPanelAccordionCollapsed] = useAtom(
    rankingPanelAccordionCollapsedAtom
  );
  return (
    <Accordion
      title={t('info.title')}
      className="py-1"
      isTopExpanding
      isCollapsed={rankingPanelAccordionCollapsed}
      setState={setRankingPanelAccordionCollapsed}
    >
      <InfoText />
      <div className="mt-4 flex flex-wrap gap-2 pb-1 ">
        <ApiButton size="md" shouldShrink />
        <DocumentationButton size="md" shouldShrink type="secondary" />
      </div>
    </Accordion>
  );
}
