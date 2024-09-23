import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';
import { FuturePriceData } from 'types';

import { FuturePrice } from './FuturePrice';

export const priceData = {
  entryCount: 24,
  priceData: {
    '2024-09-01 22:00:00+00:00': 25,
    '2024-09-01 23:00:00+00:00': 15,
    '2024-09-02 00:00:00+00:00': 12,
    '2024-09-02 01:00:00+00:00': 28,
    '2024-09-02 02:00:00+00:00': 21,
    '2024-09-02 03:00:00+00:00': 16,
    '2024-09-02 04:00:00+00:00': 19,
    '2024-09-02 05:00:00+00:00': 24,
    '2024-09-02 06:00:00+00:00': 27,
    '2024-09-02 07:00:00+00:00': 22,
    '2024-09-02 08:00:00+00:00': 13,
    '2024-09-02 09:00:00+00:00': 29,
    '2024-09-02 10:00:00+00:00': 18,
    '2024-09-02 11:00:00+00:00': 20,
    '2024-09-02 12:00:00+00:00': 26,
    '2024-09-02 13:00:00+00:00': 14,
    '2024-09-02 14:00:00+00:00': 23,
    '2024-09-02 15:00:00+00:00': 30,
    '2024-09-02 16:00:00+00:00': 17,
    '2024-09-02 17:00:00+00:00': 11,
    '2024-09-02 18:00:00+00:00': 22,
    '2024-09-02 19:00:00+00:00': 13,
    '2024-09-02 20:00:00+00:00': 28,
    '2024-09-02 21:00:00+00:00': 19,
    '2024-09-02 22:00:00+00:00': 29,
    '2024-09-02 23:00:00+00:00': 16,
    '2024-09-03 00:00:00+00:00': 24,
    '2024-09-04 01:00:00+00:00': 15,
    '2024-09-05 02:00:00+00:00': 12,
    '2024-09-06 03:00:00+00:00': 28,
    '2024-09-07 04:00:00+00:00': 21,
    '2024-09-08 05:00:00+00:00': 16,
  },
  currency: 'EUR',
  source: 'nordpool.com',
  zoneKey: 'DE',
};

describe('FuturePrice only positive values', () => {
  beforeEach(() => {
    const now = new Date('2024-09-02T02:00:00Z').getTime();
    cy.clock(now);
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <FuturePrice futurePrice={priceData as FuturePriceData}></FuturePrice>
      </I18nextProvider>
    );
  });

  it('Opens when accordion clicked', () => {
    cy.get('[data-test-id="future-price"]').should('not.exist');
    cy.get('[data-test-id="collapse-button"]').click();
    cy.get('[data-test-id="future-price"]').should('be.visible');
  });

  it('Tomorrow label is visible', () => {
    cy.get('[data-test-id="tomorrow-label"]').should('be.visible');
  });

  it('Price data is visible', () => {
    cy.get('[data-test-id="negative-price"]').should('not.exist');
    cy.get('[data-test-id="price-bar"]').should('be.visible');
    cy.get('[data-test-id="positive-price"]').should('be.visible');
  });

  it('Disclaimers are visible', () => {
    cy.get('[data-test-id="time-disclaimer"]').should('be.visible');
    cy.get('[data-test-id="price-disclaimer"]').should('be.visible');
  });

  it('now label is visible', () => {
    cy.get('[data-test-id="now-label"]').should('be.visible');
  });
});

const negativePriceData = JSON.parse(JSON.stringify(priceData));

negativePriceData.priceData['2024-09-02 03:00:00+00:00'] = -0.2;
negativePriceData.priceData['2024-09-02 13:00:00+00:00'] = -0.9;
negativePriceData.priceData['2024-09-02 08:00:00+00:00'] = -0.3;

describe('FuturePrice negative values', () => {
  beforeEach(() => {
    const now = new Date('2024-09-02T02:00:00Z').getTime();
    cy.clock(now);
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <FuturePrice futurePrice={negativePriceData as FuturePriceData}></FuturePrice>
      </I18nextProvider>
    );
  });

  it('Price data is visible', () => {
    cy.get('[data-test-id="negative-price"]').should('be.visible');
    cy.get('[data-test-id="price-bar"]').should('be.visible');
    cy.get('[data-test-id="positive-price"]').should('be.visible');
  });
});
