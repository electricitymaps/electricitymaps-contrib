# Zone Geo Generator

Computes `bounding_box` and `center_point` for each zone YAML file in `config/zones/` based on the geometries in `world.geojson`.

For aggregate zones (zones with `subZoneNames`), the geometry is computed by combining all sub-zone geometries.

## Prerequisites

- [Bun](https://bun.sh/) runtime

## Usage

```sh
# Install dependencies
bun install

# Generate/update zone geo data
bun run generate-zone-geo.ts
```

This will update all zone YAML files in `config/zones/` with computed `bounding_box` and `center_point` values.
