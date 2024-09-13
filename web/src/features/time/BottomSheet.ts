export type SnapPoint = number;

interface BottomSheetEvents {
  onOpen?: () => void;
  onClose?: () => void;
  onSnap?: (snapIndex: number) => void;
}

export interface BottomSheetProps extends BottomSheetEvents {
  snapPoints?: SnapPoint[];
  backgroundColor?: string;
  excludeElement?: HTMLElement;
}

function createBackdropElement(bgColor: string): HTMLDivElement {
  const backdrop = document.createElement('div');
  const hasTailwindBackground = bgColor.includes('bg-');

  if (!hasTailwindBackground) {
    Object.assign(backdrop.style, {
      position: 'absolute',
      left: '0',
      right: '0',
      bottom: '0',
      backgroundColor: bgColor,
      transition: 'height 0.3s ease-out',
    });
  }
  if (hasTailwindBackground) {
    Object.assign(backdrop.style, {
      position: 'absolute',
      left: '0',
      right: '0',
      bottom: '0',
      transition: 'height 0.3s ease-out',
    });
    backdrop.classList.add(bgColor);
  }

  return backdrop;
}

function getSafeAreaBottom(): number {
  const windowHeight = window.innerHeight;
  const documentHeight = document.documentElement.clientHeight;
  return windowHeight - documentHeight;
}

function isExcludedElement(props: BottomSheetProps, target: EventTarget | null): boolean {
  if (!props.excludeElement || !target) {
    return false;
  }
  return props.excludeElement.contains(target as Node);
}

export function createBottomSheet(element: HTMLElement, props: BottomSheetProps) {
  const { backgroundColor = 'white' } = props;

  const state = {
    currentSnap: 0,
    childrenHeight: 0,
    snapPointsWithChildHeight: [] as number[],
  };

  const backdropElement = createBackdropElement(backgroundColor);
  const childrenElement = element.children[0] as HTMLElement;

  function init(): () => void {
    setupElementStyles(element);
    element.append(backdropElement);
    updateChildrenHeight();
    setSnap(0);
    setupAccessibility();
    return addEventListeners();
  }

  function setupAccessibility(): void {
    element.setAttribute('role', 'dialog');
    element.setAttribute('aria-modal', 'true');
  }

  function setupElementStyles(element_: HTMLElement): void {
    Object.assign(element_.style, {
      position: 'fixed',
      bottom: '0',
      left: '0',
      right: '0',
      touchAction: 'none',
      transition: 'height 0.3s ease-out',
    });
  }

  function updateChildrenHeight(): void {
    if (childrenElement) {
      const newChildrenHeight = childrenElement.offsetHeight;
      if (newChildrenHeight !== state.childrenHeight) {
        state.childrenHeight = newChildrenHeight;
        updateBackdropPosition();
        updateSnapPoints();
        adjustCurrentSnapPoint();
      }
    }
  }

  function adjustCurrentSnapPoint(): void {
    const currentSnapValue = state.snapPointsWithChildHeight[state.currentSnap];
    if (
      currentSnapValue === state.childrenHeight ||
      state.currentSnap === state.snapPointsWithChildHeight.length - 1
    ) {
      // If the current snap point is set to the full height of the inner element,
      // or if it's the last snap point, adjust it to the new height
      setSnap(state.snapPointsWithChildHeight.length - 1);
    }
  }

  function updateSnapPoints(): void {
    if (props.snapPoints) {
      const maxSnapPoint = Math.max(...props.snapPoints);
      state.snapPointsWithChildHeight =
        state.childrenHeight > maxSnapPoint
          ? [
              ...props.snapPoints.filter((point) => point !== maxSnapPoint),
              state.childrenHeight,
            ]
          : [...props.snapPoints];
    } else {
      const safeAreaBottom = getSafeAreaBottom();
      state.snapPointsWithChildHeight = [safeAreaBottom + 60, state.childrenHeight];
    }
  }

  function updateBackdropPosition(): void {
    const currentSheetHeight =
      Number.parseFloat(element.style.height) || state.snapPointsWithChildHeight[0];
    const backdropHeight = Math.max(currentSheetHeight - state.childrenHeight + 1, 0);
    backdropElement.style.height = `${backdropHeight}px`;
    backdropElement.style.bottom = '0px';
  }

  function addEventListeners(): () => void {
    const handlers = createHandlers();
    const resizeHandler = () => {
      updateChildrenHeight();
      setSnap(state.currentSnap);
    };

    // Touch events
    element.addEventListener('touchstart', handlers.start, { passive: true });
    element.addEventListener('touchmove', handlers.move, { passive: false });
    element.addEventListener('touchend', handlers.end, { passive: true });

    // Mouse events
    element.addEventListener('mousedown', handlers.start);
    window.addEventListener('mousemove', handlers.move);
    window.addEventListener('mouseup', handlers.end);

    window.addEventListener('resize', resizeHandler);

    const resizeObserver = new ResizeObserver(updateChildrenHeight);
    resizeObserver.observe(childrenElement);

    return () => {
      element.removeEventListener('touchstart', handlers.start);
      element.removeEventListener('touchmove', handlers.move);
      element.removeEventListener('touchend', handlers.end);
      element.removeEventListener('mousedown', handlers.start);
      window.removeEventListener('mousemove', handlers.move);
      window.removeEventListener('mouseup', handlers.end);
      window.removeEventListener('resize', resizeHandler);
      resizeObserver.disconnect();
    };
  }

  function createHandlers() {
    let startY: number;
    let startHeight: number;
    let lastY: number;
    let lastTime: number;
    let velocity: number;
    let isExcludedTouch: boolean;
    let isDragging: boolean = false;

    return {
      start: (event: TouchEvent | MouseEvent) => {
        isExcludedTouch = isExcludedElement(props, event.target);
        if (isExcludedTouch) {
          return;
        }

        isDragging = true;
        startY = lastY = 'touches' in event ? event.touches[0].clientY : event.clientY;
        startHeight = element.getBoundingClientRect().height;
        lastTime = Date.now();
        velocity = 0;
        element.style.transition = 'none';
        backdropElement.style.transition = 'none';

        // Prevent text selection during drag
        event.preventDefault();
      },
      move: (event: TouchEvent | MouseEvent) => {
        if (isExcludedTouch || !isDragging) {
          return;
        }

        const currentY = 'touches' in event ? event.touches[0].clientY : event.clientY;
        const currentTime = Date.now();
        const deltaY = currentY - lastY;
        const deltaTime = currentTime - lastTime;

        if (deltaTime > 0) {
          velocity = deltaY / deltaTime;
        }

        const newHeight = calculateNewHeight(startHeight - (currentY - startY));
        setHeight(newHeight);

        lastY = currentY;
        lastTime = currentTime;

        event.preventDefault();
      },
      end: () => {
        if (isExcludedTouch || !isDragging) {
          return;
        }

        isDragging = false;
        element.style.transition = 'height 0.3s ease-out';
        backdropElement.style.transition = 'height 0.3s ease-out';
        const currentHeight = element.getBoundingClientRect().height;

        const targetSnap = determineTargetSnap(currentHeight, velocity);
        setSnap(targetSnap);
      },
    };
  }

  function determineTargetSnap(currentHeight: number, velocity: number): number {
    const closestSnapIndex = findClosestSnapIndex(currentHeight);
    const velocityThreshold = 0.5; // Adjust this value to change sensitivity

    if (Math.abs(velocity) > velocityThreshold) {
      // If flicking up
      if (velocity < 0 && closestSnapIndex < state.snapPointsWithChildHeight.length - 1) {
        return closestSnapIndex + 1;
      }
      // If flicking down
      if (velocity > 0 && closestSnapIndex > 0) {
        return closestSnapIndex - 1;
      }
    }

    // If velocity is low, or at the edges, snap to closest
    return closestSnapIndex;
  }

  function calculateNewHeight(height: number): number {
    const [lowestSnapPoint, highestSnapPoint] = [
      Math.min(...state.snapPointsWithChildHeight),
      Math.max(...state.snapPointsWithChildHeight),
    ];

    if (height >= lowestSnapPoint && height <= highestSnapPoint) {
      return height;
    }

    const rubberBandFactor = 1;
    if (height > highestSnapPoint) {
      const overscroll = height - highestSnapPoint;
      return highestSnapPoint + (1 - Math.exp(-overscroll / 200)) * 50 * rubberBandFactor;
    }

    const underscroll = lowestSnapPoint - height;
    return lowestSnapPoint - (1 - Math.exp(-underscroll / 200)) * 50 * rubberBandFactor;
  }

  function findClosestSnapIndex(currentHeight: number): number {
    let closestIndex = 0;
    let smallestDiff = Math.abs(state.snapPointsWithChildHeight[0] - currentHeight);

    for (let index = 1; index < state.snapPointsWithChildHeight.length; index++) {
      const currentDiff = Math.abs(
        state.snapPointsWithChildHeight[index] - currentHeight
      );
      if (currentDiff < smallestDiff) {
        smallestDiff = currentDiff;
        closestIndex = index;
      }
    }

    return closestIndex;
  }

  function setHeight(height: number): void {
    element.style.height = `${height}px`;
    updateBackdropPosition();
  }

  function setSnap(snapIndex: number): void {
    state.currentSnap = snapIndex;
    const snapValue = state.snapPointsWithChildHeight[snapIndex];

    setHeight(snapValue);
    props.onSnap?.(snapIndex);
    if (snapIndex === 0) {
      props.onClose?.();
    } else if (snapIndex === state.snapPointsWithChildHeight.length - 1) {
      props.onOpen?.();
    }
  }

  function snapTo(snapIndex: number): void {
    if (snapIndex >= 0 && snapIndex < state.snapPointsWithChildHeight.length) {
      setSnap(snapIndex);
    }
  }

  const removeListeners = init();

  return {
    snapTo,
    destroy: () => {
      removeListeners();
      backdropElement.remove();
      // Reset styles
      element.style.position = '';
      element.style.bottom = '';
      element.style.left = '';
      element.style.right = '';
      element.style.touchAction = '';
      element.style.transition = '';
      element.style.height = '';
      // Remove accessibility attributes
      element.removeAttribute('role');
      element.removeAttribute('aria-modal');
    },
  };
}
