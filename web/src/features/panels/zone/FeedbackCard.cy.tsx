import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import FeedbackCard from 'components/app-survey/FeedbackCard';
import { I18nextProvider } from 'react-i18next';
import i18n from 'translation/i18n';

function postSurveyResponse() {}

describe('FeedbackCard', () => {
  beforeEach(() => {
    const queryClient = new QueryClient();
    cy.mount(
      <I18nextProvider i18n={i18n}>
        <QueryClientProvider client={queryClient}>
          <FeedbackCard
            postSurveyResponse={postSurveyResponse}
            primaryQuestion={i18n.t('feedback-card.estimations.primary-question')}
            secondaryQuestionHigh={i18n.t('feedback-card.estimations.secondary-question')}
            secondaryQuestionLow={i18n.t('feedback-card.estimations.secondary-question')}
            subtitle={i18n.t('feedback-card.estimations.subtitle')}
          />
        </QueryClientProvider>
      </I18nextProvider>
    );
  });

  it('renders correctly', () => {
    cy.get('[data-testid=feedback-card]').should('be.visible');
    cy.get('[data-testid=title]').should('contain.text', 'Help us improve!');
    cy.get('[data-testid=subtitle]').should(
      'contain.text',
      'Please rate the following statement.'
    );
    cy.get('[data-testid=feedback-question]').should(
      'contain.text',
      'The description of the data estimation was easy to understand:'
    );
    cy.get('[data-testid=feedback-pill-1]').should('contain.text', '1');
    cy.get('[data-testid=feedback-pill-5]').should('contain.text', '5');
    cy.get('[data-testid=agree-text]').should('contain.text', 'Strongly agree');
    cy.get('[data-testid=disagree-text]').should('contain.text', 'Strongly disagree');
  });

  it('closes when the close button is clicked', () => {
    cy.get('[data-testid=close-button]').click();
    cy.get('[data-testid=feedback-card]').should('not.exist');
  });

  it('changes state when pill is clicked', () => {
    cy.get('[data-testid=feedback-pill-4]').click();
    cy.get('[data-testid=input-title]').should(
      'contain.text',
      'Anything we can do to improve it?'
    );
  });

  it('changes state when the submit button is clicked', () => {
    cy.get('[data-testid=feedback-pill-1]').click();
    cy.get('[data-testid=feedback-input]').type('Test comment');
    cy.get('[data-testid=pill]').click();
    cy.get('[data-testid=title]').should('contain.text', 'Thank you for your feedback!');
  });
});
