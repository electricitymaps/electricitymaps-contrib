import type { Meta, StoryObj } from '@storybook/react';
import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';
import { EstimationMethods } from 'utils/constants';

import EstimationCard, {
  EstimatedCard,
  EstimatedTSACard,
  OutageCard,
} from './EstimationCard';

const meta: Meta<typeof EstimationCard> = {
  title: 'EstimationCard',
  component: EstimationCard,
};

export default meta;
type Story = StoryObj<typeof EstimationCard>;

const instance: { message: string; issue: string } = {
  message: 'Some outage message.',
  issue: '5613',
};

export const OutageCardStory: Story = {
  render: () => (
    <I18nextProvider i18n={i18n}>
      <div className="space-y-2">
        <OutageCard zoneMessage={instance} estimationMethod={EstimationMethods.OUTAGE} />
        <OutageCard
          zoneMessage={{ message: 'Different outage message', issue: '1234' }}
          estimationMethod={EstimationMethods.THRESHOLD_FILTERED}
        />
      </div>
    </I18nextProvider>
  ),
};

export const EstimatedCardStory: Story = {
  render: () => (
    <I18nextProvider i18n={i18n}>
      <div className="space-y-2">
        <EstimatedCard estimationMethod={EstimationMethods.FORECASTS_HIERARCHY} />
        <EstimatedCard estimationMethod={EstimationMethods.THRESHOLD_FILTERED} />
      </div>
    </I18nextProvider>
  ),
};

export const EstimatedTSACardStory: Story = {
  render: () => (
    <I18nextProvider i18n={i18n}>
      <div className="space-y-2">
        <EstimatedTSACard />
      </div>
    </I18nextProvider>
  ),
};
