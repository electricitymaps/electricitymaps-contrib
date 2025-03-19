import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';
import { EstimationMethods } from 'utils/constants';

import {
  AggregatedCard,
  EstimatedCard,
  EstimatedTSACard,
  OutageCard,
} from './EstimationCard';

describe('EstimatedTSACard', () => {
  beforeEach(() => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <EstimatedTSACard />
      </I18nextProvider>
    );
  });

  it('Estimation card contains expected information', () => {
    cy.get('[data-testid=title]').contains('Data is preliminary');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The data for this hour has not been reported yet and is based on preliminary data.'
    );
  });

  it('Toggles when collapse button is clicked', () => {
    cy.get('[data-testid="collapse-up"]').should('not.exist');
    cy.get('[data-testid="collapse-down"]').should('exist');
    cy.get('[data-testid="body-text"]').should('not.exist');
    cy.get('[data-testid="methodology-link"]').should('not.exist');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="collapse-up"]').should('exist');
    cy.get('[data-testid="collapse-down"]').should('not.exist');
    cy.get('[data-testid="body-text"]').should('exist');
    cy.get('[data-testid="methodology-link"]').should('exist');
  });
});

describe('EstimatedCard', () => {
  it('Estimation card with unknown estimation method contains expected information', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <EstimatedCard estimationMethod={undefined} />
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').contains('Data is estimated');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The published data for this zone is unavailable or incomplete. The data shown on the map is estimated using our best effort, but might differ from the actual values.'
    );
  });
});

describe('OutageCard', () => {
  beforeEach(() => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <OutageCard
          estimationMethod={EstimationMethods.CONSTRUCT_BREAKDOWN}
          zoneMessage={{ message: 'Outage Message', issue: 'issue' }}
        />
      </I18nextProvider>
    );
  });

  it('Outage message contains expected information', () => {
    cy.get('[data-testid=title]').contains('Ongoing issues');
  });

  it('For outage start as expanded and toggles collapse when collapse button is clicked', () => {
    cy.get('[data-testid="collapse-up"]').should('exist');
    cy.get('[data-testid="collapse-down"]').should('not.exist');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="collapse-up"]').should('not.exist');
    cy.get('[data-testid="collapse-down"]').should('exist');
  });
});

describe('AggregatedCard', () => {
  it('Aggregated card with estimation contains expected information', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <AggregatedCard estimatedPercentage={50} />
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').contains('Data is aggregated');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The data consists of an aggregation of hourly values. 50% of the production values are estimated.'
    );
  });

  it('Aggregated card contains expected information', () => {
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <AggregatedCard estimatedPercentage={undefined} />
      </I18nextProvider>
    );
    cy.get('[data-testid=title]').contains('Data is aggregated');
    cy.get('[data-testid="collapse-button"]').click();
    cy.get('[data-testid="body-text"]').contains(
      'The data consists of an aggregation of hourly values.'
    );
  });
});
