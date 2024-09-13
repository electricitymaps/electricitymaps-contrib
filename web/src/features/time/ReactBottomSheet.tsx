import { createBottomSheet } from 'bottom-sheet-dialog';
import React, { useEffect, useRef } from 'react';

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

  useEffect(() => {
    if (bottomSheetReference.current) {
      const bottomSheet = createBottomSheet(bottomSheetReference.current, {
        snapPoints,
        backgroundColor,
        excludeElement: excludeElementRef?.current || undefined,
      });

      return () => {
        bottomSheet.destroy();
      };
    }
  }, [snapPoints, backgroundColor, excludeElementRef]);

  return <div ref={bottomSheetReference}>{children}</div>;
}
