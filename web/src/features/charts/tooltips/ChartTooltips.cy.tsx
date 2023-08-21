import { CarbonUnits } from 'utils/units';
import BreakdownChartTooltip from './BreakdownChartTooltip';
import CarbonChartTooltip from './CarbonChartTooltip';
import EmissionChartTooltip from './EmissionChartTooltip';
import { zoneDetailMock } from 'stories/mockData';

it('Carbon chart tooltip', () => {
  cy.mount(
    <CarbonChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="carbonIntensity" />
  );
  cy.contains('Carbon intensity');
  cy.contains(`187 ${CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}`);
  cy.contains('2022');
});
it('Breakdown chart tooltip', () => {
  cy.mount(
    <BreakdownChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="hydro" />
  );
  cy.contains('Hydro');
  cy.contains(`22.13 % of electricity available in`);
  cy.contains(`representing 1.26 % of emissions`);
  cy.contains('Nov');
});
it('Emmisions chart tooltip', () => {
  cy.mount(<EmissionChartTooltip zoneDetail={zoneDetailMock} />);
  cy.contains('Carbon emissions');
  cy.contains(`20.39t of CO₂eq per minute`);
  cy.contains('28');
});

it('Carbon chart tooltip mobile', () => {
  cy.viewport(500, 500);
  cy.mount(
    <CarbonChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="carbonIntensity" />
  );
  cy.contains('Carbon intensity');
  cy.contains(`187 ${CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}`);
  cy.contains('2022');
});
it('Breakdown chart tooltip mobile', () => {
  cy.viewport(500, 500);
  cy.mount(
    <BreakdownChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="hydro" />
  );
  cy.contains('Hydro');
  cy.contains(`22.13 % of electricity available in`);
  cy.contains(`representing 1.26 % of emissions`);
  cy.contains('Nov');
});
it('Emmisions chart tooltip mobile', () => {
  cy.viewport(500, 500);
  cy.mount(<EmissionChartTooltip zoneDetail={zoneDetailMock} />);
  cy.contains('Carbon emissions');
  cy.contains(`20.39t of CO₂eq per minute`);
  cy.contains('28');
});
