import React from 'react';
import styled from 'styled-components';
import Icon from '../icon';

const BackgroundOverlay = styled.div`
  height: 100%;
  width: 100%;
  position: absolute;
  left: 0;
  top: 0;
  z-index: 500;
  zoom: 1;
  filter: alpha(opacity=10);
  opacity: 0.1;
  background-color: black;

  /* @include respond-to('small') {
    opacity: 0;
  } */
`;

const ModalContainer = styled.div`
  display: flex;
  max-width: 880px;
  width: 100%;
  height: 488px;
  z-index: 999;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);

  /* @include respond-to('small') {
        width: 100%;
        left: 0;
        bottom: 56px;
        top: auto;
        transform: none;
        height: 420px; */
`;

const ModalBody = styled.div`
  flex: 1;
  position: relative;
  border-radius: 15px;
  background-color: #fafafa;
  color: white;
  max-width: 700px;
  box-shadow: 0 0 30px 0 rgba(0, 0, 0, 0.15);
`;

const ModalHeader = styled.div`
  display: grid;
  height: 90px;
  grid-template-columns: 33% 33% 33%;
  justify-items: center;
  align-items: center;
`;
const Title = styled.h1`
  color: black;
  grid-column-start: 2;
`;
const CloseButton = styled.button`
  margin-left: auto;
  margin-right: 20px;
  background-color: white;
  height: 48px;
  width: 48px;
  border: none;
  border-radius: 25px;
  transition: all 0.3s ease-in-out;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 36px;
  width: 36px;
  background-color: #333333;
`;

export const Modal = ({ title }) => {
  const handleDismiss = () => {
    // console.log('hello');
  };

  return (
    <React.Fragment>
      <BackgroundOverlay onClick={handleDismiss} />
      <ModalContainer className="modal">
        <ModalBody>
          <ModalHeader>
            <Title>{title}</Title>
            <CloseButton>
              <Icon iconName="close" color="#fff" />
            </CloseButton>
          </ModalHeader>
        </ModalBody>
      </ModalContainer>
    </React.Fragment>
  );
};
