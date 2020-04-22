import React, {
  useRef,
  useState,
  useEffect,
  useMemo,
} from 'react';
import { useSelector } from 'react-redux';
import { interpolate } from 'd3-interpolate';
import { debounce } from 'lodash';
import moment from 'moment';

import { useWidthObserver, useHeightObserver } from '../../hooks/viewport';
import { useWindEnabled } from '../../helpers/router';
import { getRefTime, getTargetTime } from '../../helpers/grib';

import Windy from '../../helpers/windy';
import global from '../../global';

const WIND_OPACITY = 0.53;

const interpolateWindData = (windData, now) => {
  const gribs1 = windData.forecasts[0];
  const gribs2 = windData.forecasts[1];
  const tBefore = getTargetTime(gribs1[0]);
  const tAfter = getTargetTime(gribs2[0]);
  if (moment(now) > tAfter) {
    console.error('Error while interpolating wind because current time is out of bounds');
    return null;
  }

  console.log(
    '#1 wind forecast target',
    tBefore.fromNow(),
    'made', getRefTime(gribs1[0]).fromNow(),
  );
  console.log(
    '#2 wind forecast target',
    tAfter.fromNow(),
    'made', getRefTime(gribs2[0]).fromNow(),
  );

  // Interpolate wind
  // const k = (now - t_before) / (t_after - t_before);
  // const interpolatedWind = gribs1;
  // interpolatedWind[0].data = gribs1[0].data.map((d, i) => interpolate(d, gribs2[0].data[i])(k));
  // interpolatedWind[1].data = gribs1[1].data.map((d, i) => interpolate(d, gribs2[1].data[i])(k));
  // return interpolatedWind;

  return gribs1;
};

const getTransformQuotient = (transformA, transformB) => {
  if (!transformA || !transformB) {
    return 'translate(0,0) scale(1)';
  }
  const k = transformA.k / transformB.k;
  const x = (k * transformB.x) - transformA.x;
  const y = (k * transformB.y) - transformA.y;
  return `translate(${x}px,${y}px) scale(${k})`;
};

const startWindy = (enabled, windy, width, height, unproject, callback) => {
  const sw = unproject([0, height]);
  const ne = unproject([width, 0]);
  windy.start(
    [[0, 0], [width, height]],
    width,
    height,
    [sw, ne],
  );
  windy.paused = false;
  if (callback) callback();
};

const debouncedStartWindy = debounce(startWindy, 500);

const WindLayer = () => {
  const ref = useRef(null);
  const width = useWidthObserver(ref);
  const height = useHeightObserver(ref);
  const enabled = useWindEnabled();

  const windData = useSelector(state => state.data.wind);

  const [windy, setWindy] = useState(null);
  const [windyRunning, setWindyRunning] = useState(false);

  const [isDragging, setIsDragging] = useState(false);
  const [dragFromTransform, setDragFromTransform] = useState(null);
  const [dragToTransform, setDragToTransform] = useState(null);

  const project = useMemo(
    () => global.zoneMap && global.zoneMap.projection(),
    [global.zoneMap],
  );
  const unproject = useMemo(
    () => global.zoneMap && global.zoneMap.unprojection(),
    [global.zoneMap],
  );

  // Set up map interaction handlers.
  useEffect(() => {
    if (global.zoneMap) {
      global.zoneMap
        .onDragStart((transform) => {
          setIsDragging(true);
          setDragFromTransform(transform);
          setDragToTransform(transform);
        })
        .onDrag((transform) => {
          setDragToTransform(transform);
        })
        .onDragEnd(() => {
          setIsDragging(false);
          setDragFromTransform(null);
          setDragToTransform(null);
        });
    }
  }, [global.zoneMap]);

  useEffect(() => {
    if (enabled && windy && unproject) {
      if (isDragging) {
        debouncedStartWindy.cancel();
        windy.paused = true;
      } else {
        debouncedStartWindy(enabled, windy, width, height, unproject);
      }
    }
  }, [enabled, windy, width, height, unproject, isDragging]);

  // Create a Windy instance if it's not been created yet.
  useEffect(() => {
    if (ref.current && enabled && !windy && windData) {
      const data = interpolateWindData(windData, undefined);
      setWindy(new Windy({
        canvas: ref.current,
        data,
        project,
        unproject,
      }));
    } else if (!enabled) {
      setWindy(null);
    }
  }, [ref.current, enabled, windy, windData]);

  // Start / stop Windy rendering engine.
  useEffect(() => {
    if (windy && !windyRunning && enabled) {
      startWindy(enabled, windy, width, height, unproject);
      setWindyRunning(true);
    } else if (windy && windyRunning && !enabled) {
      windy.stop();
      setWindyRunning(false);
    }
  }, [enabled, windy, windyRunning, width, height]);

  return (
    <canvas
      ref={ref}
      className="map-layer wind"
      style={{
        display: enabled ? 'block' : 'none',
        opacity: enabled ? WIND_OPACITY : 0,
        transform: getTransformQuotient(dragToTransform, dragFromTransform),
      }}
      width={width}
      height={height}
    />
  );
};

export default WindLayer;
