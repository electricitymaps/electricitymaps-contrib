declare module 'use-react-screenshot' {
  const useScreenshot: () => [string | null, (node: HTMLElement) => Promise<string>];
  export { useScreenshot };
}
