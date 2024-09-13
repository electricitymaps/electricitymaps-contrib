import React, { useEffect, useRef, useState } from 'react';

import { createBottomSheet } from './BottomSheet';

interface ReactBottomSheetProps {
  children: React.ReactNode;
  snapPoints?: number[];
  backgroundColor?: string;
  excludeElementRef?: React.RefObject<HTMLElement>;
}

export function ReactBottomSheet({
  children,
  snapPoints,
  backgroundColor = 'white',
  excludeElementRef,
}: ReactBottomSheetProps) {
  const bottomSheetReference = useRef<HTMLDivElement>(null);
  const bottomSheetInstanceReference = useRef<ReturnType<
    typeof createBottomSheet
  > | null>(null);
  const [currentSnapIndex, setCurrentSnapIndex] = useState(0);

  useEffect(() => {
    if (bottomSheetReference.current) {
      bottomSheetInstanceReference.current = createBottomSheet(
        bottomSheetReference.current,
        {
          snapPoints,
          backgroundColor,
          excludeElement: excludeElementRef?.current || undefined,
          onSnap: (snapIndex) => {
            setCurrentSnapIndex(snapIndex);
          },
        }
      );

      return () => {
        if (bottomSheetInstanceReference.current) {
          bottomSheetInstanceReference.current.destroy();
        }
      };
    }
  }, [snapPoints, backgroundColor, excludeElementRef]);

  useEffect(() => {
    if (bottomSheetInstanceReference.current) {
      bottomSheetInstanceReference.current.snapTo(currentSnapIndex);
    }
  }, [snapPoints, currentSnapIndex]);

  return <div ref={bottomSheetReference}>{children}</div>;
}
