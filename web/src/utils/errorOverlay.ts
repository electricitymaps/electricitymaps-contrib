// Source: https://github.com/vitejs/vite/issues/2076#issuecomment-846558772
const showErrorOverlay = (error: Error) => {
  // Must be within function call because that's when the element is defined for sure.
  const ErrorOverlay = customElements.get('vite-error-overlay');
  // Don't open outside vite environment
  if (!ErrorOverlay) {
    return;
  }
  console.log(error);
  const overlay = new ErrorOverlay(error);
  document.body.append(overlay);
};

export default function enableErrorsInOverlay() {
  window.addEventListener('error', ({ error }) => showErrorOverlay(error));
  window.addEventListener('unhandledrejection', ({ reason }) => showErrorOverlay(reason));
}
