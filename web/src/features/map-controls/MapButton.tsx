import { Button } from 'components/Button';

import TooltipWrapper from '../../components/tooltips/TooltipWrapper';

interface MapButtonProperties {
  onClick?: () => void;
  icon: JSX.Element;
  tooltipText?: string;
  className?: string;
  dataTestId?: string;
  ariaLabel?: string;
  backgroundClasses?: string;
}

export default function MapButton({
  icon,
  tooltipText,
  dataTestId,
  onClick,
  ariaLabel,
  backgroundClasses,
}: MapButtonProperties) {
  return (
    <TooltipWrapper tooltipContent={tooltipText} asChild={false}>
      <Button
        size="md"
        type="transparent"
        icon={icon}
        onClick={onClick}
        aria-label={ariaLabel}
        data-test-id={dataTestId}
        backgroundClasses={backgroundClasses}
      />
    </TooltipWrapper>
  );
}
