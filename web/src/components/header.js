import styled from 'styled-components';

const HeaderContent = styled.div`
  display: flex;
  width: 100%;
  font-size: 1.0rem;
  height: 50px;
  padding-top: 13px;
  padding-bottom: 13px;
  padding-left: 15px;
  padding-right: 15px;
  line-height: 24px;

  /* Force width to include padding */
  box-sizing: border-box;

  & > div,
  & > span {
      vertical-align: middle;
  }
`;

export {
  HeaderContent,
};
