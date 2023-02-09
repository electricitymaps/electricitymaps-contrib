// This is a fallback component for Sentry.ErrorBoundary, so sending errors to Sentry
// is not necessary here. This is only for showing a message to users.
// See more: https://docs.sentry.io/platforms/javascript/guides/react/features/error-boundary/

interface Props {
  error: Error;
  componentStack: string | null;
  resetError: () => void;
}

export default function ErrorComponent({ error }: Props) {
  const url = window.location.href;
  return (
    <div className="flex w-full flex-col items-center justify-center">
      <h1>Oh no, something went wrong...</h1>
      <p>
        Please let us know{' '}
        <a href="https://github.com/electricityMaps/electricitymaps-contrib">on Github</a>{' '}
        so we can fix this!
      </p>
      <pre className="rounded-lg bg-gray-300 p-2 text-xs dark:bg-black">
        Error message: {error?.toString()}
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
}
