import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | undefined;
}

class ErrorComponent extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: undefined,
  };

  public static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI.
    return { hasError: true, error: error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // TODO: Send this to Sentry https://linear.app/electricitymaps/issue/ELE-1366/set-up-proper-sentry-process
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    const url = window.location.href;
    return (
      <div className="flex w-full flex-col items-center justify-center">
        <h1>Oh no, something went wrong...</h1>
        <p>
          Please let us know{' '}
          <a href="https://github.com/electricityMaps/electricitymaps-contrib">
            on Github
          </a>{' '}
          so we can fix this!
        </p>
        <pre className="rounded-lg bg-gray-300 p-2 text-xs">
          Error message: {this.state.error?.message}
          <br />
          Url: {url}
        </pre>
        <a
          href="/map"
          className="mt-4 cursor-pointer rounded-lg border border-gray-200 bg-gray-100 p-2 text-base text-black"
        >
          Back to map
        </a>
        <pre className="mt-4 whitespace-normal text-center text-xs">
          App version: {APP_VERSION}
          <br />
          {navigator.userAgent}
        </pre>
      </div>
    );

    return this.props.children;
  }
}

export default ErrorComponent;
