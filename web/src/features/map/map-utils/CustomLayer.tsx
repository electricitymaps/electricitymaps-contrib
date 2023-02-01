/* eslint-disable unicorn/no-null */
/* eslint-disable unicorn/consistent-function-scoping */
import { IControl } from 'mapbox-gl';
import React, { useState } from 'react';
import { MapboxMap, useControl } from 'react-map-gl';

class OverlayControl implements IControl {
  _map: MapboxMap | null = null;
  _container: HTMLElement | undefined;
  _redraw: () => void;

  constructor(redraw: () => void) {
    this._redraw = redraw;
  }

  onAdd(map: MapboxMap) {
    this._map = map;
    map.on('move', this._redraw);
    /* global document */
    this._container = document.createElement('div');
    this._redraw();
    return this._container;
  }

  onRemove() {
    this._container?.remove();
    this._map?.off('move', this._redraw);
    this._map = null;
  }

  getMap() {
    return this._map;
  }

  getElement() {
    return this._container;
  }
}

// see https://github.com/visgl/react-map-gl/blob/master/examples/custom-overlay/src/custom-overlay.tsx

function CustomLayer(props: { children: React.ReactElement }) {
  const [, setVersion] = useState(0);

  const ctrl = useControl<OverlayControl>(() => {
    const forceUpdate = () => setVersion((v) => v + 1);
    return new OverlayControl(forceUpdate);
  });

  const map = ctrl.getMap();

  return map && React.cloneElement(props.children, { map });
}

export default React.memo(CustomLayer);
