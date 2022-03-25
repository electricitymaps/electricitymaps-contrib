import React from 'react';
import { useParams } from 'react-router-dom';

import zonesConfig from '../../../config/zones.json';

const getContributorId = (contributor) => {
  const contributorSplitted = contributor.split('/');
  return contributorSplitted[contributorSplitted.length-1];
}

const ContributorList = () => {
  const { zoneId } = useParams();
  const contributors = (zonesConfig[zoneId] || {}).contributors || [];

  return (
    <div className="contributors">
      {contributors.map(contributor => {
        const contributorId = getContributorId(contributor);
    
        return (
          <a key={contributorId} href={contributor} rel="noopener noreferrer" target="_blank">
            <img src={`https://avatars.githubusercontent.com/${contributorId}?s=40`} alt={contributorId} />
          </a>
        )
      })}
    </div>
  );
};

export default ContributorList;
