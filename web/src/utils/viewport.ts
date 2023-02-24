import { useCallback, useState } from 'react';

// TODO: Replace with https://github.com/ZeeCoder/use-resize-observer
export function useReferenceWidthHeightObserver(offsetX = 0, offsetY = 0) {
  const [width, setWidth] = useState(0);
  const [height, setHeight] = useState(0);
  const [node, setNode] = useState<Element | null>(null); // The DOM node

  // See https://reactjs.org/docs/hooks-faq.html#how-can-i-measure-a-dom-node
  const reference = useCallback(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (newNode: Element | null) => {
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
    },
    [offsetX, offsetY]
  );

  return {
    ref: reference,
    width,
    height,
    node,
  };
}
