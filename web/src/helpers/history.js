import {
  flatMap,
  keys,
  sortBy,
  uniq,
} from 'lodash';

import { dispatchApplication } from '../store';

export function getExchangeKeys(zoneHistory) {
  return sortBy(uniq(flatMap(zoneHistory, d => keys(d.exchange))));
}

export function createGraphMouseMoveHandler() {
  return (timeIndex) => {
    dispatchApplication('selectedZoneTimeIndex', timeIndex);
  };
}

export function createGraphMouseOutHandler() {
  return () => {
    dispatchApplication('selectedZoneTimeIndex', null);
  };
}

export function createGraphLayerMouseMoveHandler(isMobile, setSelectedLayerIndex) {
  return (timeIndex, layerIndex, layer, ev, svgRef) => {
    // If in mobile mode, put the tooltip to the top of the screen for
    // readability, otherwise float it depending on the cursor position.
    const tooltipPosition = !isMobile
      ? { x: ev.clientX - 7, y: svgRef.current.getBoundingClientRect().top - 7 }
      : { x: 0, y: 0 };
    if (setSelectedLayerIndex) {
      setSelectedLayerIndex(layerIndex);
    }
    dispatchApplication('tooltipPosition', tooltipPosition);
    dispatchApplication('tooltipZoneData', layer.datapoints[timeIndex].data._countryData);
    dispatchApplication('tooltipDisplayMode', layer.key);
    dispatchApplication('selectedZoneTimeIndex', timeIndex);
  };
}

export function createGraphLayerMouseOutHandler(setSelectedLayerIndex) {
  return () => {
    if (setSelectedLayerIndex) {
      setSelectedLayerIndex(null);
    }
    dispatchApplication('tooltipDisplayMode', null);
  };
}
