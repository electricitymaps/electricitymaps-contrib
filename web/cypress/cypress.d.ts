import { mount } from 'cypress/react';

// Augment the Cypress namespace to include type definitions for
// your custom command.
// Alternatively, can be defined in cypress/support/component.d.ts
// with a <reference path="./component" /> at the top of your spec.
declare global {
  namespace Cypress {
    interface Chainable {
      mount: typeof mount;
      setSliderValue: (value: number) => Chainable<void>;
      interceptAPI: (path: string) => void;
      waitForAPISuccess: (path: string) => void;
      visitOnMobile: (path: string) => void;
      getById: (value: string, arguments_?: any) => Chainable<JQuery<HTMLElement>>;
    }
  }
}
