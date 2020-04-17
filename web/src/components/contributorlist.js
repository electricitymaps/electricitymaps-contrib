import React from 'react';
import { useParams } from 'react-router-dom';

import zonesConfig from '../../../config/zones.json';

const ContributorList = () => {
  const { zoneId } = useParams();
  const contributors = (zonesConfig[zoneId] || {}).contributors || [];

  return (
    <div className="contributors">
      {contributors.map(contributor => (
        <a key={contributor} href={contributor} rel="noopener noreferrer" target="_blank">
          <img src={`${contributor}.png`} alt={contributor} />
        </a>
      ))}
    </div>
  );
};

export default ContributorList;
