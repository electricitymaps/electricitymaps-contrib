import { useState, useEffect, useCallback } from 'react';

export function useRefWidthHeightObserver(offsetX = 0, offsetY = 0) {
  const [width, setWidth] = useState(0);
  const [height, setHeight] = useState(0);
  const [node, setNode] = useState(null); // The DOM node

  // See https://reactjs.org/docs/hooks-faq.html#how-can-i-measure-a-dom-node
  const ref = useCallback(
    (newNode) => {
      // This callback will be called once the ref
      // returned has been attached to `node`.
      const update = () => {
        if (newNode !== null) {
          const newWidth = newNode.getBoundingClientRect().width - offsetX;
          const newHeight = newNode.getBoundingClientRect().height - offsetY;
          setWidth(newWidth);
          setHeight(newHeight);
          setNode(newNode);
        }
      };
      // Set initial width (the usage of setTimeout solves race conditions on mobile)
      setTimeout(() => {
        update();
      }, 0);
      // Update container width on every resize
      window.addEventListener('resize', update);
      return () => {
        window.removeEventListener('resize', update);
      };
    },
    [offsetX, offsetY]
  );

  return {
    ref,
    width,
    height,
    node,
  };
}

export function useWindowSize() {
  const [windowSize, setWindowSize] = useState({});

  // Resize hook
  useEffect(() => {
    const updateSize = () => {
      if (windowSize.width !== window.innerWidth || windowSize.height !== window.innerHeight) {
        setWindowSize({
          width: window.innerWidth,
          height: window.innerHeight,
        });
      }
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
