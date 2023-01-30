import { scaleLinear } from 'd3-scale';

const SOLAR_STEPS = [0, 500, 1000];
const MAX_SOLAR = SOLAR_STEPS.at(-1) as number;

// Note: This custom function replaces our usage of the color-parse library.
export const splitRGBA = (rgba: string) => {
  const [red, green, blue, alpha] = rgba
    .replace('rgba(', '')
    .replace('rgb(', '')
    .replace(')', '')
    .split(',') // Split into array
    .map((value) => Number.parseFloat(value));
  return [red, green, blue, alpha || 1];
};

// Scale
export const solarColor = scaleLinear<string>()
  .domain(SOLAR_STEPS)
  .range(['rgba(0,0,0,1)', 'rgba(0,0,0,0)', 'rgba(255,215,0,1)'])
  .clamp(true);

export const solarIntensityToOpacity = (intensity: number) =>
  Math.floor((intensity / MAX_SOLAR) * 255);
export const opacityToSolarIntensity = (opacity: number) =>
  Math.floor((opacity * MAX_SOLAR) / 255);

// Pre-process solar color components across all integer values
// for faster vertex shading when generating the canvas image.
export const solarColorComponents = [...Array.from({ length: MAX_SOLAR + 1 }).keys()].map(
  (value) => {
    const parsed = splitRGBA(solarColor(value));
    return {
      red: parsed[0],
      green: parsed[1],
      blue: parsed[2],
      alpha: Math.floor(255 * 0.85 * parsed[3]), // Max layer opacity 85%
    };
  }
);
