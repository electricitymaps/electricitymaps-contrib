import { extent } from 'd3-array';
import { scaleLinear, scaleQuantize } from 'd3-scale';
import { colors } from 'hooks/colors';
import { MapColorSource } from 'utils/constants';

// The following are the values in which the arrowfiles are generated
const arrowfileCount = 10;
export const arrowfilesIndices = Array.from(
  { length: arrowfileCount },
  (_, index) => index + 1
);

export function generateQuantizedExchangeColorScale(mapColorSource: MapColorSource) {
  // Assume the domain (i.e. values) are the same for colorblind and normal mode
  let domain = extent(colors.bright.colorScale[mapColorSource].domain());
  if (!domain) {
    return;
  }
  let range = arrowfilesIndices;
  // scaleQuantize only supports ascending domains
  if (domain[0] > domain[1]) {
    range = range.toReversed();
    domain = domain.toReversed();
  }
  return scaleQuantize().domain(domain).range(range).unknown('nan');
}

export const quantizedExchangeSpeedScale = scaleLinear()
  .domain([500, 5000])
  .rangeRound([0, 2])
  .unknown(0)
  .clamp(true);
