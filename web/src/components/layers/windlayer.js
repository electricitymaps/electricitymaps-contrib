import React, {
  useRef,
  useState,
  useEffect,
  useLayoutEffect,
  useMemo,
} from 'react';
import { CSSTransition } from 'react-transition-group';
import styled from 'styled-components';

import { useWidthObserver, useHeightObserver } from '../../hooks/viewport';
import { useWindEnabled } from '../../helpers/router';

import global from '../../global';
import Windy from '../../helpers/windy';
import { useInterpolatedWindData } from '../../hooks/layers';

const Canvas = styled.canvas`
  top: 0;
  left: 0;
  pointer-events: none;
  position: absolute;
  transition: opacity 300ms ease-in-out;
  width: 100%;
  height: 100%;
`;

export default () => {
  const ref = useRef(null);
  const width = useWidthObserver(ref);
  const height = useHeightObserver(ref);
  const interpolatedData = useInterpolatedWindData();
  const enabled = useWindEnabled();

  const [windy, setWindy] = useState(null);

  const [isInitialized, setIsInitialized] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const project = useMemo(
    () => global.zoneMap && global.zoneMap.projection(),
    [global.zoneMap],
  );
  const unproject = useMemo(
    () => global.zoneMap && global.zoneMap.unprojection(),
    [global.zoneMap],
  );
  const viewport = useMemo(
    () => {
      if (!unproject) return null;
      const sw = unproject([0, height]);
      const ne = unproject([width, 0]);
      return [
        [[0, 0], [width, height]],
        width,
        height,
        [sw, ne],
      ];
    },
    [width, height, unproject],
  );

  // Set up map interaction handlers once the map gets initialized.
  useEffect(() => {
    if (global.zoneMap && !isInitialized) {
      global.zoneMap
        .onDragStart((transform) => {
          setIsDragging(true);
        })
        .onDragEnd(() => {
          setIsDragging(false);
          setIsReady(false);
        });
      setIsInitialized(true);
    }
  }, [global.zoneMap, isInitialized]);

  // Create a Windy instance if it's not been created yet.
  useEffect(() => {
    if (!windy && enabled && ref.current && interpolatedData && viewport) {
      setIsReady(false);
      setWindy(new Windy({
        canvas: ref.current,
        data: interpolatedData,
        project,
        unproject,
      }));
    } else if (windy && !enabled) {
      windy.stop();
      setWindy(null);
    }
  }, [windy, enabled, ref.current, interpolatedData, viewport]);

  useLayoutEffect(() => {
    if (enabled && windy && viewport && !isReady) {
      setTimeout(() => {
        windy.start(...viewport);
        setTimeout(() => {
          setIsReady(true);
        }, 500);
      }, 0);
    }
  }, [enabled, windy, viewport, isReady]);

  return (
    <CSSTransition
      classNames="fade"
      in={enabled && isReady && !isDragging}
      timeout={300}
    >
      <Canvas
        id="wind"
        width={width}
        height={height}
        ref={ref}
      />
    </CSSTransition>
  );
};
