import ExchangeTooltip from './ExchangeTooltip';

const data = {
  rotation: 90,
  lonlat: [75, 75] as [number, number],
  key: 'DK-DK1->DK-DK2',
  f: 200,
  ci: 120,
};

it('mounts', () => {
  cy.mount(<ExchangeTooltip exchangeData={data} isMobile={false} />);
  cy.contains('Denmark');
  cy.contains('→');
});

it('mounts on mobile', () => {
  cy.viewport('iphone-6');
  cy.mount(<ExchangeTooltip exchangeData={data} isMobile />);
  cy.contains('Denmark');
  cy.contains('↓');
});
