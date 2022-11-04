import LeftPanel from './LeftPanel';

describe('<LeftPanel>', () => {
  it('mounts', () => {
    cy.mount(<LeftPanel />);
    cy.contains('hi there');
  });
});
