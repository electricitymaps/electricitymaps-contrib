import React from 'react';
import styled from 'styled-components';

const OpenPositionsBadgeWrapper = styled.div`
  background-color: #f20050;
  border-radius: 50px;
  color: #fff;
  font-size: 11px;
  font-weight: bold;
  height: 20px;
  line-height: 20px;
  display: inline-block;
  text-align: center;
  margin-left: 4px;
  transition: width 0.2s ease-in-out;
  width: ${(props) => (props.shouldShow ? '20px' : '0px')};
  && {
    text-shadow: none;
  }
`;

const OpenPositionsBadge = () => {
  const [positions, setPositions] = React.useState(null);

  // Fetch the RSS feed to get the number of open positions
  React.useEffect(() => {
    fetch('https://electricitymap.org/jobs/rss.xml')
      .then((res) => res.text())
      .then((str) => new window.DOMParser().parseFromString(str, 'text/xml'))
      .then((data) => {
        const items = data.getElementsByTagName('item');
        const openPositions = items ? items.length : null;
        setPositions(openPositions);
      })
      .catch(() => console.error('Failed fetching open positions count'));
  }, []);

  return <OpenPositionsBadgeWrapper shouldShow={positions > 0}>{positions}</OpenPositionsBadgeWrapper>;
};

export default OpenPositionsBadge;
