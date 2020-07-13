import { useState, useEffect } from 'react';

export function useWidthObserver(ref, offset = 0) {
  const [width, setWidth] = useState(0);

  // Resize hook
  useEffect(() => {
    const updateWidth = () => {
      if (ref.current) {
        const newWidth = ref.current.getBoundingClientRect().width - offset;
        if (newWidth !== width) { setWidth(newWidth); }
      }
    };
    // Set initial width
    updateWidth();
    // Update container width on every resize
    window.addEventListener('resize', updateWidth);
    return () => {
      window.removeEventListener('resize', updateWidth);
    };
  });

  return width;
}

export function useHeightObserver(ref, offset = 0) {
  const [height, setHeight] = useState(0);

  // Resize hook
  useEffect(() => {
    const updateHeight = () => {
      if (ref.current) {
        const newHeight = ref.current.getBoundingClientRect().height - offset;
        if (newHeight !== height) { setHeight(newHeight); }
      }
    };
    // Set initial height
    updateHeight();
    // Update height on every resize
    window.addEventListener('resize', updateHeight);
    return () => {
      window.removeEventListener('resize', updateHeight);
    };
  });

  return height;
}

function useWindowSize() {
  const [windowSize, setWindowSize] = useState({});

  // Resize hook
  useEffect(() => {
    const updateSize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };
    // Set initial size
    updateSize();
    // Add window listeners
    window.addEventListener('resize', updateSize);
    return () => {
      window.removeEventListener('resize', updateSize);
    };
  });

  return windowSize;
}

export function useIsSmallScreen() {
  const { width } = useWindowSize();
  return width < 768;
}

export function useIsMediumUpScreen() {
  const { width } = useWindowSize();
  return width >= 768;
}
