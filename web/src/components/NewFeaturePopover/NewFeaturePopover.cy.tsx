import { NewFeaturePopover } from './NewFeaturePopover';

describe('New Feature Popover', () => {
  it('should display', () => {
    cy.mount(
      <NewFeaturePopover side="bottom" content={<p>content</p>} isOpenByDefault={true}>
        <p className="w-fit">anchor</p>
      </NewFeaturePopover>
    );
    cy.contains('content');
  });

  it('should display anchor if no content', () => {
    cy.mount(
      <NewFeaturePopover content="" side="bottom" isOpenByDefault={true}>
        <p>anchor</p>
      </NewFeaturePopover>
    );
    cy.contains('anchor');
    cy.contains('content').should('not.exist');
  });

  it('should close on dismiss', () => {
    cy.mount(
      <NewFeaturePopover side="bottom" content={<p>content</p>} isOpenByDefault={true}>
        <p>anchor</p>
      </NewFeaturePopover>
    );
    cy.contains('anchor');
    cy.get('[data-test-id=dismiss]').click();
    cy.contains('content').should('not.exist');
  });
});
