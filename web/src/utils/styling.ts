import { useLayoutEffect, useState } from 'react';

type Breakpoint = 'sm' | 'md' | 'lg' | 'xl' | '2xl';

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => matchMedia(query).matches);

  useLayoutEffect(() => {
    const mediaQuery = matchMedia(query);

    function onMediaQueryChange(): void {
      setMatches(mediaQuery.matches);
    }

    mediaQuery.addEventListener('change', onMediaQueryChange);

    return (): void => {
      mediaQuery.removeEventListener('change', onMediaQueryChange);
    };
  }, [query]);

  return matches;
}

export function useBreakpoint(breakpoint: Breakpoint) {
  const queries = {
    sm: '(min-width: 640px)',
    md: '(min-width: 768px)',
    lg: '(min-width: 1024px)',
    xl: '(min-width: 1280px)',
    '2xl': '(min-width: 1536px)',
  };
  return useMediaQuery(queries[breakpoint]);
}
