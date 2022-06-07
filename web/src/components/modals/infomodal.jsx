import React from 'react';
import styled from 'styled-components';
import { useTranslation } from '../../helpers/translation';

const ModalBackground = styled.div`
  display: flex;
  flex-direction: column;
  /* max-width: 880px; */
  width: 100%;
  height: 100%;
  z-index: 999;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
`;

const Title = styled.h1`
  font-size: 26px;
`;
const Description = styled.p`
  text-align: center;
  font-size: 12px;
`;
const Wrapper = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
`;
const ButtonWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-direction: column;
  height: 100%;
  margin-bottom: 50px;
  margin-top: 12px;
`;

const StyledButton = styled.button`
  border-radius: 50px;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  width: 250px;
  height: 55px;
  text-align: center;
  margin-bottom: 12px;
  font-weight: bold;
  box-shadow: rgba(149, 157, 165, 0.2) 0px 8px 24px;
`;

const getPathText = (name) => `${resolvePath(`images/${name}`)}`; // TODO: remove

const StyledIcon = styled.i`
  background-image: url(${(props) => getPathText(props.iconName)});
  height: 16px;
  width: 16px;
  background-repeat: no-repeat;
  background-size: contain;
  margin-right: 5px;
`;

const InfoButton = ({ children, className, iconName }) => {
  return (
    <StyledButton className={className}>
      <StyledIcon iconName={iconName} />
      {children}
    </StyledButton>
  );
};

const FeedBackButton = styled(InfoButton)`
  background-color: #44ab60;
`;
const FAQButton = styled(InfoButton)`
  background-color: white;
  color: black;
  box-shadow: rgba(149, 157, 165, 0.2) 0px 8px 24px;
`;
const OpenSourceButton = styled(InfoButton)`
  background: linear-gradient(90deg, #04275c, #040e23);
`;
const TwitterShareButton = styled(InfoButton)`
  background-color: #1d9bf0;
`;
const SlackButton = styled(InfoButton)`
  background-color: #4a154b;
`;

const CloseIcon = styled.i`
  position: absolute;
  background-image: url(${(_) => getPathText('closebutton.svg')});
  top: 30px;
  right: 30px;
  height: 15px;
  width: 15px;
  color: red;
  background-repeat: no-repeat;
  background-size: contain;
`;

const InfoModal = () => {
  const { __ } = useTranslation();

  return (
    <ModalBackground>
      <CloseIcon iconName="closebutton.svg" />
      <Wrapper>
        <Title>{__('info-modal.title')}</Title>
        <Description>{__('info-modal.description')}</Description>
        <Description
          dangerouslySetInnerHTML={{
            __html: __(
              'info-modal.description2',
              'https://electricitymap.org/open-source/?utm_source=app.electricitymap.org&utm_medium=referral'
            ),
          }}
        />
      </Wrapper>
      <ButtonWrapper>
        <div>
          <FeedBackButton iconName="feedback.svg">Share your feedback</FeedBackButton>
          <FAQButton iconName="faq.svg">FAQ</FAQButton>
        </div>
        <div>
          <OpenSourceButton iconName="opensource.svg">Open Source</OpenSourceButton>
          <TwitterShareButton iconName="twitter.svg">Share the app on Twitter</TwitterShareButton>
          <SlackButton iconName="slack.png">Join the Slack community</SlackButton>
        </div>
      </ButtonWrapper>
    </ModalBackground>
  );
};

export default InfoModal;
