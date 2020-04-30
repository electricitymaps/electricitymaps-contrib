import React from 'react';
import { BaseControl } from 'react-map-gl';

// A proxy component that passes the projection methods to layers
// based on the current map state. Setting _containerRef in a wrapper
// is important for capturing mouse events (e.g. clicks) and not
// letting them propagate to the map.
class MapLayer extends BaseControl {
  _render() {
    return (
      <div ref={this._containerRef}>
        <this.props.component
          project={this._context.viewport.project}
          unproject={this._context.viewport.unproject}
        />
      </div>
    );
  }
}

// Pass through all drag events to the map.
MapLayer.defaultProps.captureDrag = false;

export default MapLayer;
