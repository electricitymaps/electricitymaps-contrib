/* eslint-disable @typescript-eslint/unbound-method, @typescript-eslint/no-unsafe-member-access, @typescript-eslint/no-unsafe-call */

/*
 * NOTE: Remember to declare custom commands in cypress.d.ts!
 * Otherwise you will see cryptic TS errors like: "Argument of type '"YOUR_COMMAND"' is not
 * assignable to parameter of type 'keyof Chainable<any>'.ts(2345)"
 */

/**
 * The setSliderValue command will set the value of a input[type=range] element.
 * See https://github.com/cypress-io/cypress/issues/1570#issuecomment-891244917
 */
// TODO: DISABLED FOR NOW AS IT WAS CAUSING PROBLEMS AND HARD TO TYPE
// Cypress.Commands.add('setSliderValue', { prevSubject: 'element' }, (subject, value) => {
//   const element = subject[0] as HTMLInputElement;
//   cy.window().then((win) => {
//     const nativeInputValueSetter = Object.getOwnPropertyDescriptor(win.HTMLInputElement.prototype, 'value')?.set;
//     nativeInputValueSetter?.call(element, value);
//     element.dispatchEvent(new Event('input', { bubbles: true }));
//   });
// });

// Source: https://github.com/cypress-io/cypress-realworld-app/blob/develop/cypress/support/commands.ts#L34
Cypress.Commands.add('getById', (value, ...arguments_) => {
  return cy.get(`[data-test=${value}]`, ...arguments_);
});

Cypress.Commands.add('interceptAPI', (path) => {
  const [pathWithoutParameters, parameters] = path.split('?');
  let fixturePath = pathWithoutParameters;
  // Change fixture path if countryCode query parameter is used to use correct response
  if (parameters && parameters.includes('countryCode')) {
    const zone = parameters.split('=')[1];
    fixturePath = pathWithoutParameters.replace(
      '/history/hourly',
      `/history/${zone}/hourly`
    );
  }
  cy.intercept('GET', `**/${path}`, {
    fixture: `${fixturePath}.json`,
  }).as(path);
});

Cypress.Commands.add('waitForAPISuccess', (path) => {
  cy.wait(`@${path}`)
    .its('response.statusCode')
    .should('match', /200|304/);
});

Cypress.Commands.add('visitOnMobile', (path) => {
  cy.viewport('iphone-6');
  cy.visit(path, {
    onBeforeLoad: (win) => {
      // @ts-ignore
      win.addEventListener('touchstart', true);
      Object.defineProperty(win.navigator, 'userAgent', {
        value:
          'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
      });
    },
  });
});
