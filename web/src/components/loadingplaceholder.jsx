import styled from 'styled-components';

export default styled.div`
  background: transparent url(${resolvePath('images/loading/loading64_FA.gif')}) no-repeat center center;
  background-size: 1.7rem;
  display: inline-block;
  height: ${(props) => props.height || '100%'};
  width: 100%;
`;
