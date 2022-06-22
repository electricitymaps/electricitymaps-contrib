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
Cypress.Commands.add('setSliderValue', { prevSubject: 'element' }, (subject, value) => {
  const element = subject[0];

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

Cypress.Commands.add('interceptAPI', (path) => {
  const pathWithoutParams = path.split('?')[0];
  cy.intercept('GET', `http://localhost:8001/${path}`, {
    fixture: `${pathWithoutParams}.json`,
  }).as(path);
});
Cypress.Commands.add('waitForAPISuccess', (path) => {
  cy.wait(`@${path}`)
    .its('response.statusCode')
    .should('match', /200|304/);
});
