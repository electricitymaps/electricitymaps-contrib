import React from 'react';
import styled from 'styled-components';
import { useTranslation } from '../helpers/translation';

const ModalBackground = styled.div`
  display: flex;
  flex-direction: column;
  max-width: 880px;
  width: 100%;
  height: 100%;
  z-index: 999;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
`;

const Title = styled.h1``;
const Description = styled.p``;
const Wrapper = styled.div`
  display: flex;
  justify-content: center;
  flex-direction: column;
`;

const InfoButton = styled.button`
  border-radius: 20px;
  background-color: ${(props) => props.backgroundColor};
`;

const InfoModal = () => {
  const { __ } = useTranslation();

  return (
    <ModalBackground>
      <Wrapper>
        <Title>{__('info-modal.title')}</Title>
        <Description>{__('info-modal.description')}</Description>
      </Wrapper>
      <Wrapper>
        <InfoButton backgroundColor="#44AB60">Share your feedback</InfoButton>
        <InfoButton backgroundColor="white">Share your feedback</InfoButton>
        <InfoButton backgroundColor="#04275C">Open Source</InfoButton>
        <InfoButton backgroundColor="#04275C">Share the app on twitter</InfoButton>
        <InfoButton backgroundColor="#04275C">Join the Slack Community</InfoButton>
      </Wrapper>
    </ModalBackground>
  );
};

export default InfoModal;
