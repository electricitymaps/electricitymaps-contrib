// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add('login', (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add('drag', { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add('dismiss', { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This will overwrite an existing command --
// Cypress.Commands.overwrite('visit', (originalFn, url, options) => { ... })

/**
 * The setSliderValue command will set the value of a input[type=range] element.
 * See https://github.com/cypress-io/cypress/issues/1570#issuecomment-891244917
 */
// @ts-expect-error TS(2769): No overload matches this call.
Cypress.Commands.add('setSliderValue', { prevSubject: 'element' }, (subject, value) => {
  const element = (subject as any)[0];

  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;

  nativeInputValueSetter?.call(element, value);
  element.dispatchEvent(new Event('input', { bubbles: true }));
});
// TypeScript declaration for future use
// declare namespace Cypress {
//     interface Chainable {
//         setSliderValue(value: number): Chainable<void>
//     }
// }

// @ts-expect-error TS(2345): Argument of type '"interceptAPI"' is not assignabl... Remove this comment to see the full error message
Cypress.Commands.add('interceptAPI', (path) => {
  const [pathWithoutParams, params] = (path as any).split('?');
  let fixturePath = pathWithoutParams;
  // Change fixture path if countryCode query parameter is used to use correct response
  if (params && params.includes('countryCode')) {
    const zone = params.split('=')[1];
    fixturePath = pathWithoutParams.replace('/history/hourly', `/history/${zone}/hourly`);
  }
  cy.intercept('GET', `http://localhost:8001/${path}`, {
    fixture: `${fixturePath}.json`,
    // @ts-expect-error TS(2345): Argument of type 'unknown' is not assignable to pa... Remove this comment to see the full error message
  }).as(path);
});
// @ts-expect-error TS(2345): Argument of type '"waitForAPISuccess"' is not assi... Remove this comment to see the full error message
Cypress.Commands.add('waitForAPISuccess', (path) => {
  cy.wait(`@${path}`)
    .its('response.statusCode')
    .should('match', /200|304/);
});

// @ts-expect-error TS(2345): Argument of type '"visitOnMobile"' is not assignab... Remove this comment to see the full error message
Cypress.Commands.add('visitOnMobile', (path) => {
  cy.viewport('iphone-6');
  // @ts-expect-error TS(2345): Argument of type 'unknown' is not assignable to pa... Remove this comment to see the full error message
  cy.visit(path, {
    onBeforeLoad: (win) => {
      // @ts-expect-error TS(2322): Type 'boolean' is not assignable to type '((this: ... Remove this comment to see the full error message
      win.ontouchstart = true;
      Object.defineProperty(win.navigator, 'userAgent', {
        value:
          'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
      });
    },
  });
});
