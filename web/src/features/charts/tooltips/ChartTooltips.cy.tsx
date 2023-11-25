import { zoneDetailMock } from 'stories/mockData';
import { CarbonUnits } from 'utils/units';

import BreakdownChartTooltip from './BreakdownChartTooltip';
import CarbonChartTooltip from './CarbonChartTooltip';
import EmissionChartTooltip from './EmissionChartTooltip';

it('Carbon chart tooltip', () => {
  cy.mount(
    <CarbonChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="carbonIntensity" />
  );
  cy.contains('Carbon intensity');
  cy.contains(`213 ${CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}`);
  cy.contains('2023');
});
it('Breakdown chart tooltip', () => {
  cy.mount(
    <BreakdownChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="hydro" />
  );
  cy.contains('Hydro');
  cy.contains(`16.33 % of electricity available in`);
  cy.contains(`representing 0.82 % of emissions`);
  cy.contains('Sep');
});
it('Emmisions chart tooltip', () => {
  cy.mount(<EmissionChartTooltip zoneDetail={zoneDetailMock} />);
  cy.contains('Carbon emissions');
  cy.contains(`1.42 kt of CO₂eq`);
  cy.contains('5');
});

it('Carbon chart tooltip mobile', () => {
  cy.viewport(500, 500);
  cy.mount(
    <CarbonChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="carbonIntensity" />
  );
  cy.contains('Carbon intensity');
  cy.contains(`213 ${CarbonUnits.GRAMS_CO2EQ_PER_WATT_HOUR}`);
  cy.contains('2023');
});
it('Breakdown chart tooltip mobile', () => {
  cy.viewport(500, 500);
  cy.mount(
    <BreakdownChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="hydro" />
  );
  cy.contains('Hydro');
  cy.contains(`16.33 % of electricity available in`);
  cy.contains(`representing 0.82 % of emissions`);
  cy.contains('Sep');
});
it('Emmisions chart tooltip mobile', () => {
  cy.viewport(500, 500);
  cy.mount(<EmissionChartTooltip zoneDetail={zoneDetailMock} />);
  cy.contains('Carbon emissions');
  cy.contains(`1.42 kt of CO₂eq`);
  cy.contains('5');
});
