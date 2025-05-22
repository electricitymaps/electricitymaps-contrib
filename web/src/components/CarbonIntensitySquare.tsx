import { animated, useSpring } from '@react-spring/web';
import { ScaleLinear } from 'd3-scale';
import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  MapColorSource,
  mapColorSourceTranslationKeys,
  unitsByMapColorSource,
} from 'utils/constants';

import { useCo2ColorScale } from '../hooks/theme';
import InfoIconWithPadding from './InfoIconWithPadding';
import LabelTooltip from './tooltips/LabelTooltip';
import TooltipWrapper from './tooltips/TooltipWrapper';

/**
 * This function finds the optimal text color based on a custom formula
 * derived from the W3CAG standard (see https://www.w3.org/TR/WCAG20-TECHS/G17.html).
 * I changed the original formula from Math.sqrt(1.05 * 0.05) - 0.05 to
 * Math.sqrt(1.05 * 0.18) - 0.05. Because this expression is a constant
 * I replaced it with it's approached value (0.3847...) to avoid useless computations.
 * See https://github.com/electricitymaps/electricitymaps-contrib/issues/3365 for more informations.
 * @param {string} rgbColor a string with the background color (e.g. "rgb(0,5,4)")
 */
const getTextColor = (rgbColor: string) => {
  const colors = rgbColor.replaceAll(/[^\d,.]/g, '').split(',');
  const r = Number.parseInt(colors[0], 10);
  const g = Number.parseInt(colors[1], 10);
  const b = Number.parseInt(colors[2], 10);
  const rgb = [r, g, b].map((c) => {
    const s = c / 255;
    return s <= 0.039_28 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
  });
  const luminosity = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
  return luminosity >= 0.384_741_302_385_683_16 ? 'black' : 'white';
};

function CarbonIntensitySquare({
  intensity,
  tooltipContent,
}: CarbonIntensitySquareProps) {
  const co2ColorScale = useCo2ColorScale();

  return (
    <ValueSquare
      value={intensity}
      colorScale={co2ColorScale}
      tooltipContent={tooltipContent}
      unitShort={'g'}
      unitRest={unitsByMapColorSource[MapColorSource.CARBON_INTENSITY].slice(1)}
      translationKey={mapColorSourceTranslationKeys[MapColorSource.CARBON_INTENSITY]}
    />
  );
}

interface CarbonIntensitySquareProps {
  intensity: number;
  tooltipContent?: string | JSX.Element;
}

export function ValueSquare({
  value,
  colorScale,
  tooltipContent,
  unitRest,
  translationKey,
  unitShort,
}: {
  value: number;
  colorScale: ScaleLinear<string, string, string>;
  tooltipContent?: string | JSX.Element;
  unitRest: string;
  translationKey: string;
  unitShort: string;
}) {
  const { t } = useTranslation();
  const [{ backgroundColor }] = useSpring(
    {
      backgroundColor: colorScale(value),
    },
    [colorScale, value]
  );

  return (
    <div className="flex flex-col items-center gap-2">
      <TooltipWrapper
        tooltipContent={
          <LabelTooltip className="max-w-[200px]">{tooltipContent}</LabelTooltip>
        }
        side="bottom"
        sideOffset={8}
      >
        <div className="relative flex flex-col items-center">
          <div className="size-20 p-1">
            <animated.div
              style={{
                color: getTextColor(colorScale(value)),
                backgroundColor,
              }}
              className="flex h-full w-full flex-col items-center justify-center rounded-2xl"
            >
              <p
                className="select-none text-base leading-none"
                data-testid="co2-square-value"
              >
                <span className="font-semibold">
                  {Number.isFinite(value) ? Math.round(value) : '?'}
                </span>
                <span className="text-xs font-semibold">{unitShort}</span>
              </p>
              <div className="text-xxs font-semibold leading-none">{unitRest}</div>
            </animated.div>
          </div>
          {tooltipContent && <InfoIconWithPadding />}
        </div>
      </TooltipWrapper>
      <p className="text-xs font-semibold text-neutral-600 dark:text-neutral-400">
        {t(translationKey)}
      </p>
    </div>
  );
}

export default memo(CarbonIntensitySquare);
