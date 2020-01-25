import React from 'react';
import { connect } from 'react-redux';

import zonesConfig from '../../../config/zones.json';

const mapStateToProps = state => ({
  contributors: (zonesConfig[state.application.selectedZoneName] || {}).contributors || [],
});

const ContributorList = ({ contributors }) => (
  <div className="contributors">
    {contributors.map(contributor => (
      <a key={contributor} href={contributor} rel="noopener noreferrer" target="_blank">
        <img src={`${contributor}.png`} alt={contributor} />
      </a>
    ))}
  </div>
);

export default connect(mapStateToProps)(ContributorList);
