import React, { useState, useEffect, useMemo } from 'react';
import { useSelector } from 'react-redux';
// @ts-expect-error TS(7016): Could not find a declaration file for module 'reac... Remove this comment to see the full error message
import { CSSTransition } from 'react-transition-group';
import styled from 'styled-components';

import { useRefWidthHeightObserver } from '../../hooks/viewport';
import { useWindEnabled } from '../../hooks/router';

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

export default ({ project, unproject }: any) => {
  const { ref, width, height, node } = useRefWidthHeightObserver();
  const interpolatedData = useInterpolatedWindData();
  const enabled = useWindEnabled();

  const [windy, setWindy] = useState(null);

  const isMapLoaded = useSelector((state) => !(state as any).application.isLoadingMap);
  const isMoving = useSelector((state) => (state as any).application.isMovingMap);
  const isVisible = enabled && isMapLoaded && !isMoving;

  const viewport = useMemo(() => {
    const sw = unproject([0, height]);
    const ne = unproject([width, 0]);
    return [
      [
        [0, 0],
        [width, height],
      ],
      width,
      height,
      [sw, ne],
    ];
  }, [unproject, width, height]);

  // Kill and reinitialize Windy every time the layer visibility changes, which
  // will usually be at the beginning and the end of dragging. Windy initialization
  // is currently very slow so we take it to the next render cycle so that the
  // rendering of everything else is not blocked. This will hopefully be less
  // hacky once Windy service is merged here and perhaps optimized via WebGL.
  // See https://github.com/tmrowco/electricitymap-contrib/issues/944.
  useEffect(() => {
    if (!windy && isVisible && node && interpolatedData) {
      // @ts-expect-error TS(7009): 'new' expression, whose target lacks a construct s... Remove this comment to see the full error message
      const w = new Windy({
        canvas: node,
        data: interpolatedData,
        project,
        unproject,
      });
      w.start(...viewport);
      // Set in the next render cycle.
      setTimeout(() => {
        setWindy(w);
      }, 0);
    } else if (windy && !isVisible) {
      (windy as any).stop();
      setWindy(null);
    }
  }, [windy, isVisible, node, interpolatedData, project, unproject, viewport]);

  return (
    <CSSTransition classNames="fade" in={isVisible && windy && (windy as any).started} timeout={300}>
      <Canvas id="wind" width={width} height={height} ref={ref} />
    </CSSTransition>
  );
};
