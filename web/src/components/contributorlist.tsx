import React from 'react';
import { useParams } from 'react-router-dom';

import zonesConfig from '../../../config/zones.json';

const ContributorList = () => {
  const { zoneId } = useParams();

  return (
    <div className="contributors">
      {zonesConfig[zoneId]?.contributors?.map((contributor) => {
        return (
          <a key={contributor} href={`https://github.com/${contributor}`} rel="noopener noreferrer" target="_blank">
            <img
              src={`https://avatars.githubusercontent.com/${contributor}?s=20`} // loads the avatar image at a default size of 20px
              srcSet={`https://avatars.githubusercontent.com/${contributor}?s=40 2x`} // loads the avatar image at a default size of 40px for high resolution displays
              alt={contributor}
              height="20"
              width="20"
              loading="lazy" // makes sure the image don't load until the user scrolls down
            />
          </a>
        );
      })}
    </div>
  );
};

export default ContributorList;
