import type { Meta, StoryObj } from '@storybook/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';
import { EstimationMethods } from 'utils/constants';

import EstimationCard from './EstimationCard';

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
const queryClient = new QueryClient();

export const All: Story = {
  render: () => (
    <div className="space-y-2">
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <EstimationCard cardType="outage" zoneMessage={instance} />
          <EstimationCard
            cardType="outage"
            zoneMessage={instance}
            estimationMethod={EstimationMethods.THRESHOLD_FILTERED}
          />
          <EstimationCard cardType="estimated" zoneMessage={instance} />

          <EstimationCard
            cardType="estimated"
            zoneMessage={instance}
            estimationMethod={EstimationMethods.MODE_BREAKDOWN}
          />

          <EstimationCard
            cardType="aggregated"
            zoneMessage={instance}
            estimatedPercentage={20}
          />

          <EstimationCard cardType="aggregated" zoneMessage={instance} />
        </QueryClientProvider>
      </I18nextProvider>
    </div>
  ),
};
