import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { zoneDetailMock } from 'stories/mockData';
import { CarbonUnits } from 'utils/units';

import BreakdownChartTooltip from './BreakdownChartTooltip';
import CarbonChartTooltip from './CarbonChartTooltip';
import EmissionChartTooltip from './EmissionChartTooltip';

describe('Chart Tooltips', () => {
  const queryClient = new QueryClient();

  function TestWrapper({ children }: any) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter>{children}</MemoryRouter>
      </QueryClientProvider>
    );
  }

  it('Carbon chart tooltip', () => {
    cy.mount(
      <TestWrapper>
        <CarbonChartTooltip
          zoneDetail={zoneDetailMock}
          selectedLayerKey="carbonIntensity"
        />
      </TestWrapper>
    );
    cy.contains('Carbon intensity');
    cy.contains(`213 ${CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR}`);
    cy.contains('2023');
  });

  it('Breakdown chart tooltip', () => {
    cy.mount(
      <TestWrapper>
        <BreakdownChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="hydro" />
      </TestWrapper>
    );
    cy.contains('Hydro');
    cy.contains(`16.33 % of electricity available in`);
    cy.contains(`representing 0.82 % of emissions`);
    cy.contains('Sep');
  });

  it('Emissions chart tooltip', () => {
    cy.mount(
      <TestWrapper>
        <EmissionChartTooltip zoneDetail={zoneDetailMock} />
      </TestWrapper>
    );
    cy.contains('Emissions');
    cy.contains(`1.42 kt of CO₂eq`);
    cy.contains('5');
  });

  it('Carbon chart tooltip mobile', () => {
    cy.viewport(500, 500);
    cy.mount(
      <TestWrapper>
        <CarbonChartTooltip
          zoneDetail={zoneDetailMock}
          selectedLayerKey="carbonIntensity"
        />
      </TestWrapper>
    );
    cy.contains('Carbon intensity');
    cy.contains(`213 ${CarbonUnits.GRAMS_CO2EQ_PER_KILOWATT_HOUR}`);
    cy.contains('2023');
  });

  it('Breakdown chart tooltip mobile', () => {
    cy.viewport(500, 500);
    cy.mount(
      <TestWrapper>
        <BreakdownChartTooltip zoneDetail={zoneDetailMock} selectedLayerKey="hydro" />
      </TestWrapper>
    );
    cy.contains('Hydro');
    cy.contains(`16.33 % of electricity available in`);
    cy.contains(`representing 0.82 % of emissions`);
    cy.contains('Sep');
  });

  it('Emissions chart tooltip mobile', () => {
    cy.viewport(500, 500);
    cy.mount(
      <TestWrapper>
        <EmissionChartTooltip zoneDetail={zoneDetailMock} />
      </TestWrapper>
    );
    cy.contains('Emissions');
    cy.contains(`1.42 kt of CO₂eq`);
    cy.contains('5');
  });
});
