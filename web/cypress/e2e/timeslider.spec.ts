// import dailyData from '../../../mockserver/public/v10/details/daily/DK-DK2.json';
import hourlyData from '../../../mockserver/public/v10/details/hourly/DK-DK2.json';
import monthlyData from '../../../mockserver/public/v10/details/monthly/DK-DK2.json';
// import yearlyData from '../../../mockserver/public/v10/details/yearly/DK-DK2.json';

// TODO: For some reason the project's date formatter
// cannot be imported (webpack compilation error) here
// import { formatDate } from '../../src/utils/formatting';

// TODO: Convert to component test

interface Data {
  zoneStates: {
    [key: string]: {
      co2intensity: number;
      stateDatetime: string;
    };
  };
}

const getco2intensity = (index: number, data: Data) => {
  return `${Math.round(
    Object.values(data.zoneStates).at(index)?.co2intensity ?? Number.NaN
  )}`;
};

// const getFormattedDate = (index: number, data: Data, format: string) => {
//   const stateDatetime = new Date(
//     Object.values(data.data.zoneStates)[index].stateDatetime
//   );
//   return formatDate(stateDatetime, 'en', format);
// };

// const getTime = (index, date) => {
//   return new Date(date.data.zoneStates[index].stateDatetime).getTime();
// };

describe('TimeController', () => {
  beforeEach(() => {
    cy.interceptAPI('v10/meta');
  });
  it('interacts with the timecontroller on map', () => {
    // Intercepts all API network requests and serves fixtures directly
    cy.interceptAPI('v10/state/hourly');
    cy.interceptAPI('v10/details/hourly/DK-DK2');
    cy.interceptAPI('v10/state/daily');
    cy.interceptAPI('v10/state/monthly');
    cy.interceptAPI('v10/state/yearly');
    cy.interceptAPI('v10/details/daily/DK-DK2');
    cy.interceptAPI('v10/details/monthly/DK-DK2');
    cy.interceptAPI('v10/details/yearly/DK-DK2');

    // Note that we force language here as CI and local machines might display dates differently otherwise
    cy.visit('/zone/DK-DK2?lang=en-GB');
    cy.get('[data-testid=loading-overlay]').should('not.exist');
    cy.get('[data-testid=close-modal]').click();
    // Hourly
    cy.waitForAPISuccess(`v10/state/hourly`);
    cy.waitForAPISuccess(`v10/details/hourly/DK-DK2`);
    cy.contains('LIVE');
    cy.get('[data-testid=co2-square-value').should(
      'contain.text',
      getco2intensity(71, hourlyData)
    );
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(24, hourlyData, 'hourly')
    // );
    // cy.get('input.time-slider-input').setSliderValue(getTime(5, hourlyData));
    // cy.get('[data-testid=co2-square-value').should(
    //   'have.text',
    //   getco2intensity(5, hourlyData)
    // );

    // Monthly
    cy.get('[data-testid="time-controller-3mo"]').click();
    cy.waitForAPISuccess(`v10/state/daily`);
    cy.waitForAPISuccess(`v10/details/daily/DK-DK2`);
    // cy.get('[data-testid=co2-square-value').should(
    //   'contain.text',
    //   getco2intensity(30, dailyData)
    // );
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(30, dailyData, 'daily')
    // );
    //cy.get('input.time-slider-input').setSliderValue(getTime(16, dailyData));
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(16, dailyData, 'daily')
    // );
    // cy.get('[data-testid=co2-square-value').should(
    //   'have.text',
    //   getco2intensity(16, dailyData)
    // );

    // Yearly
    cy.get('[data-testid="time-controller-12mo"]').click();
    cy.waitForAPISuccess(`v10/state/monthly`);
    cy.waitForAPISuccess(`v10/details/monthly/DK-DK2`);
    cy.get('[data-testid=co2-square-value').should(
      'contain.text',
      getco2intensity(12, monthlyData)
    );
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(11, monthlyData, 'monthly')
    // );
    // //cy.get('input.time-slider-input').setSliderValue(getTime(5, monthlyData));
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(5, monthlyData, 'monthly')
    // );
    // cy.get('[data-testid=co2-square-value').should(
    //   'have.text',
    //   getco2intensity(5, monthlyData)
    // );

    // 5 Years
    // TODO: Fix this test once we have a toggle in the UI
    //cy.get('[data-testid="time-controller-all"]').click();
    //cy.waitForAPISuccess(`v10/state/yearly`);
    //cy.waitForAPISuccess(`v10/details/yearly/DK-DK2`);
    //cy.get('[data-testid=co2-square-value').should(
    //  'contain.text',
    //  getco2intensity(-1, yearlyData)
    //);
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(4, yearlyData, 'yearly')
    // );
    // //cy.get('input.time-slider-input').setSliderValue(getTime(2, yearlyData));
    // cy.get('[data-testid=date-display').should(
    //   'have.text',
    //   getFormattedDate(2, yearlyData, 'yearly')
    // );
    // cy.get('[data-testid=co2-square-value').should(
    //   'have.text',
    //   getco2intensity(2, yearlyData)
    // );
  });

  // TODO: Figure out how to get open/drag bottom sheet in Cypress on mobile
  // I have tried a bunch of combinations with mousemove, etc. without success
  it.skip('interacts with the timecontroller on mobile', () => {
    cy.visitOnMobile('/zone/DK-DK2?lang=en-GB');
  });
});
