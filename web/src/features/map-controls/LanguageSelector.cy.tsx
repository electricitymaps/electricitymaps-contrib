import { useRef, useState } from 'react';
import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';

import { LanguageSelector } from './LanguageSelector';

it('mounts and selects a language', () => {
  // Create a wrapper component to handle the isInSettings and parentRef props
  function LanguageSelectorWrapper() {
    const [isOpen, setIsOpen] = useState(false);
    const buttonReference = useRef<HTMLButtonElement>(null);

    return (
      <div>
        <button
          ref={buttonReference}
          onClick={() => setIsOpen(!isOpen)}
          data-testid="language-selector-open-button"
        >
          Select Language
        </button>
        {isOpen && (
          <LanguageSelector
            parentRef={buttonReference}
            onClose={() => setIsOpen(false)}
          />
        )}
      </div>
    );
  }

  cy.mount(
    <I18nextProvider i18n={i18n}>
      <LanguageSelectorWrapper />
    </I18nextProvider>
  );

  cy.get('[data-testid=language-selector-open-button]').click();
  cy.contains('English');
  cy.contains('Français');
  cy.contains('Deutsch');
  cy.contains('Español');
  cy.contains('Italiano');
  cy.contains('Nederlands');
  cy.contains('Polski');
  cy.contains('Português');
  cy.contains('Svenska');
  cy.contains('中文');
  cy.contains('日本語');
  cy.contains('한국어');

  cy.get('button').contains('Italiano').click();

  // We don't check for tooltips since they're not part of the new implementation
});
