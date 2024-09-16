import Accordion from 'components/Accordion';
import { GithubButton } from 'components/buttons/GithubButton';
import { LinkedinButton } from 'components/buttons/LinkedinButton';
import { RedditButton } from 'components/buttons/RedditButton';
import { SlackButton } from 'components/buttons/SlackButton';
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
      <div className="mt-4 flex flex-wrap gap-2 ">
        <SlackButton size="sm" shouldShrink />
        <GithubButton size="sm" shouldShrink />
        <LinkedinButton size="sm" shouldShrink />
        <RedditButton size="sm" shouldShrink />
      </div>
    </Accordion>
  );
}
