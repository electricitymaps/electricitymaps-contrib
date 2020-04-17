import { useState, useEffect } from 'react';

export function useWidthObserver(ref, offset = 0) {
  const [width, setWidth] = useState(0);

  // Resize hook
  useEffect(() => {
    const updateWidth = () => {
      if (ref.current) {
        setWidth(ref.current.getBoundingClientRect().width - offset);
      }
    };
    // Initialize width if it's not set yet
    if (!width) {
      updateWidth();
    }
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
        setHeight(ref.current.getBoundingClientRect().height - offset);
      }
    };
    // Initialize height if it's not set yet
    if (!height) {
      updateHeight();
    }
    // Update height on every resize
    window.addEventListener('resize', updateHeight);
    return () => {
      window.removeEventListener('resize', updateHeight);
    };
  });

  return height;
}
