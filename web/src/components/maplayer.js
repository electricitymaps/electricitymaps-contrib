import React from 'react';
import { BaseControl } from 'react-map-gl';

// A proxy component that passes the projection
// methods to layers based on the current map state.
class MapLayer extends BaseControl {
  _render() {
    return (
      <this.props.component
        project={this._context.viewport.project}
        unproject={this._context.viewport.unproject}
      />
    );
  }
}

export default MapLayer;
