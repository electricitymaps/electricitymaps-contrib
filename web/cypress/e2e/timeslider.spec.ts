import dailyData from '../../../mockserver/public/v5/history/daily.json';
import hourlyData from '../../../mockserver/public/v5/history/DK-DK2/hourly.json';
import monthlyData from '../../../mockserver/public/v5/history/monthly.json';
import yearlyData from '../../../mockserver/public/v5/history/yearly.json';
//import { formatDate } from '../../src/helpers/formatting';

// TODO: Convert to component test

// Temporary mock function until we have a proper formatDate func in place
const formatDate = (date: Date, lang: string, format: string) => {
  cy.log(`Called formatDate with ${date.toISOString()}, ${lang}, ${format}`);
  return 'date';
};

interface Data {
  data: {
    zoneStates: {
      [index: number]: {
        co2intensity: number;
        stateDatetime: string;
      };
    };
  };
}

const getco2intensity = (index: number, data: Data) => {
  return Math.round(data.data.zoneStates[index].co2intensity);
};

const getFormattedDate = (index: number, data: Data, format: string) => {
  return formatDate(new Date(data.data.zoneStates[index].stateDatetime), 'en-GB', format);
};

// const getTime = (index, date) => {
//   return new Date(date.data.zoneStates[index].stateDatetime).getTime();
// };

describe('TimeController', () => {
  it('interacts with the timecontroller on map', () => {
    // Intercepts all API network requests and serves fixtures directly
    cy.interceptAPI('v5/state/hourly');
    cy.interceptAPI('v5/history/hourly?countryCode=DK-DK2');
    cy.interceptAPI('v5/state/daily');
    cy.interceptAPI('v5/state/monthly');
    cy.interceptAPI('v5/state/yearly');
    cy.interceptAPI('v5/history/daily?countryCode=DK-DK2');
    cy.interceptAPI('v5/history/monthly?countryCode=DK-DK2');
    cy.interceptAPI('v5/history/yearly?countryCode=DK-DK2');

    // Note that we force language here as CI and local machines might display dates differently otherwise
    cy.visit('/zone/DK-DK2?skip-onboarding=true&lang=en-GB');

    // Hourly
    cy.waitForAPISuccess(`v5/state/hourly`);
    cy.waitForAPISuccess(`v5/history/hourly?countryCode=DK-DK2`);
    cy.contains('LIVE');
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(24, hourlyData)
    );
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(24, hourlyData, 'hourly')
    );
    //cy.get('input.time-slider-input').setSliderValue(getTime(5, hourlyData));
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(5, hourlyData, 'hourly')
    );
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(5, hourlyData)
    );

    // Monthly
    cy.get('[data-test-id="time-controls-daily-btn"]').click();
    cy.waitForAPISuccess(`v5/state/daily`);
    cy.waitForAPISuccess(`v5/history/daily?countryCode=DK-DK2`);
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(30, dailyData)
    );
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(30, dailyData, 'daily')
    );
    //cy.get('input.time-slider-input').setSliderValue(getTime(16, dailyData));
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(16, dailyData, 'daily')
    );
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(16, dailyData)
    );

    // Yearly
    cy.get('[data-test-id="time-controls-monthly-btn"]').click();
    cy.waitForAPISuccess(`v5/state/monthly`);
    cy.waitForAPISuccess(`v5/history/monthly?countryCode=DK-DK2`);
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(11, monthlyData)
    );
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(11, monthlyData, 'monthly')
    );
    //cy.get('input.time-slider-input').setSliderValue(getTime(5, monthlyData));
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(5, monthlyData, 'monthly')
    );
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(5, monthlyData)
    );

    // 5 Years
    cy.get('[data-test-id="time-controls-yearly-btn"]').click();
    cy.waitForAPISuccess(`v5/state/yearly`);
    cy.waitForAPISuccess(`v5/history/yearly?countryCode=DK-DK2`);
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(4, yearlyData)
    );
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(4, yearlyData, 'yearly')
    );
    //cy.get('input.time-slider-input').setSliderValue(getTime(2, yearlyData));
    cy.get('[data-test-id=date-display').should(
      'have.text',
      getFormattedDate(2, yearlyData, 'yearly')
    );
    cy.get('[data-test-id=co2-square-value').should(
      'have.text',
      getco2intensity(2, yearlyData)
    );
  });

  // TODO: Figure out how to get open/drag bottom sheet in Cypress on mobile
  // I have tried a bunch of combinations with mousemove, etc. without success
  it.skip('interacts with the timecontroller on mobile', () => {
    cy.visitOnMobile('/?skip-onboarding=true');
  });
});
