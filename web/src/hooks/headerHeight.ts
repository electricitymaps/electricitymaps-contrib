import { useEffect, useState } from 'react';

export const useHeaderHeight = (): number => {
  const [headerHeight, setHeaderHeight] = useState<number>(0);

  useEffect(() => {
    const updateHeaderHeight = () => {
      const headerElement = document.querySelector('header');
      if (headerElement) {
        const height = headerElement.offsetHeight;
        setHeaderHeight(height * 1.1);
      }
    };

    updateHeaderHeight();

    // Add resize event listener
    window.addEventListener('resize', updateHeaderHeight);

    // Cleanup event listener on unmount
    return () => {
      window.removeEventListener('resize', updateHeaderHeight);
    };
  }, []);

  return headerHeight;
};
