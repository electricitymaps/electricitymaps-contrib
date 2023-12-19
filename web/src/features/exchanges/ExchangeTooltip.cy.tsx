import ExchangeTooltip from './ExchangeTooltip';

const data = {
  rotation: 90,
  lonlat: [75, 75] as [number, number],
  key: 'DK-DK1->DK-DK2',
  f: 200,
  ci: 120,
};

it('mounts', () => {
  cy.mount(<ExchangeTooltip exchangeData={data} />);
  cy.contains('Denmark');
});
