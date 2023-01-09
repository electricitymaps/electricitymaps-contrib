// The "core" integration test that ensures everything roughly works.
// This could potentially replace most of the other e2e tests we have!
describe('app', () => {
  it('Should render the map', () => {
    // Open website on root
    cy.visit('/');
    // See the logo and header
    // See onboarding and close it
    // See the map (with colors if possible?)

    // If possible, click a country and verify URL change
    // Test that map controls work (zoom, pan, etc - but this will also be covered by component test)

    // Test FAQ
    // Test mobile modals
    // Test timeslider
  });
  it('Should render the left panel', () => {
    // Open website on root
    cy.visit('/');

    // See the left panel
    // See ranking text in panel
    // Close the panel

    // Go to a zone
    // See the zone name and details in the panel
  });
});
