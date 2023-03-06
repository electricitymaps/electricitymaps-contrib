import { TimeAverages } from 'utils/constants';
import EmissionChart from '../EmissionChart';

it('render EmissionChart', () => {
  cy.mount(<EmissionChart datetimes={[]} timeAverage={TimeAverages.DAILY} />);
});
