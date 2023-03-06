import ExchangeTooltip from './ExchangeTooltip';
const data = {
  rotation: 90,
  lonlat: [75, 75] as [number, number],
  key: 'DK-DK1->DK-DK2',
  netFlow: 200,
  co2intensity: 120,
};

it('mounts', () => {
  cy.mount(<ExchangeTooltip exchangeData={data} />);
  cy.contains('Denmark');
});
