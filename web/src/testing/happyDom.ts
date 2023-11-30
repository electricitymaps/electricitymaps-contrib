// eslint-disable-next-line import/no-extraneous-dependencies
import { GlobalRegistrator } from '@happy-dom/global-registrator';
// eslint-disable-next-line import/no-extraneous-dependencies
import mediaQuery from 'css-mediaquery';

GlobalRegistrator.register();

Object.defineProperty(window, 'IS_REACT_ACT_ENVIRONMENT', {
  writable: true,
  value: true,
});
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => {
    function matchQuery(): boolean {
      return mediaQuery.match(query, {
        width: window.innerWidth,
        height: window.innerHeight,
      });
    }

    const listeners: (() => void)[] = [];
    const instance = {
      matches: matchQuery(),
      addEventListener: (_: 'change', listener: () => void): void => {
        listeners.push(listener);
      },
      removeEventListener: (_: 'change', listener: () => void): void => {
        const index = listeners.indexOf(listener);
        if (index >= 0) {
          listeners.splice(index, 1);
        }
      },
    };
    window.addEventListener('resize', () => {
      const change = matchQuery();
      if (change !== instance.matches) {
        instance.matches = change;
        for (const listener of listeners) {
          listener();
        }
      }
    });

    return instance;
  },
});
Object.defineProperty(window, 'scrollTo', {
  writable: true,
  value: () => {},
});
Object.defineProperty(window, 'resizeTo', {
  writable: true,
  value: (width: number, height: number) => {
    Object.assign(window, {
      innerWidth: width,
      innerHeight: height,
    }).dispatchEvent(new Event('resize'));
  },
});
