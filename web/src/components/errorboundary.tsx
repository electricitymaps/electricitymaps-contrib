import React from 'react';
import styled from 'styled-components';

const ErrorBox = styled.div`
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: center;
  flex-direction: column;
`;

const ErrorMessage = styled.pre`
  font-size: 0.8rem;
  background: #e0e0e0;
  border-radius: 8px;
  padding: 8px;
  font-family: monospace;
`;

const BackToStartButton = styled.a`
  background: #fafafa;
  color: #000;
  border: 1px solid #eee;

  font-size: 1rem;
  border-radius: 8px;
  padding: 8px;
  margin-top: 16px;
  cursor: pointer;
  &:hover {
    background: #eee;
    text-decoration: none;
  }
`;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // TODO: Send this to Sentry
    console.error(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const url = window.location.href;
      return (
        <ErrorBox>
          <h1>Oh no, something went wrong...</h1>
          <p>
            Please let us know <a href="https://github.com/electricitymap/electricitymap-contrib">on Github</a> so we
            can fix this!
          </p>
          <ErrorMessage>
            Error message: {this.state.error.message}
            <br />
            Url: {url}
          </ErrorMessage>
          <BackToStartButton href="/map">Back to map</BackToStartButton>
        </ErrorBox>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
