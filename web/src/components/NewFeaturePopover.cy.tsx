import { NewFeaturePopover } from './NewFeaturePopover';

describe('New Feature Popover', () => {
  it('should display', () => {
    cy.mount(
      <NewFeaturePopover side="bottom" content={<p>content</p>} isOpen>
        <p className="w-fit">anchor</p>
      </NewFeaturePopover>
    );
    cy.contains('content');
  });

  it('should display anchor if no content', () => {
    cy.mount(
      <NewFeaturePopover content="" side="bottom" isOpen>
        <p>anchor</p>
      </NewFeaturePopover>
    );
    cy.contains('anchor');
    cy.contains('content').should('not.exist');
  });

  it('should use a portal by default', () => {
    cy.mount(
      <div className="flex justify-items-center">
        <NewFeaturePopover side="bottom" content={<p>content</p>} isOpen>
          <p>anchor</p>
        </NewFeaturePopover>
      </div>
    );
    cy.contains('anchor');
  });

  it('should not use a portal if specified', () => {
    cy.mount(
      <NewFeaturePopover side="bottom" content={<p>content</p>} portal={false} isOpen>
        <p>anchor</p>
      </NewFeaturePopover>
    );
    cy.contains('anchor');
  });
});
